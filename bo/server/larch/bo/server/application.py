"""Provides an Application object as base for specfic larch.ui Applications."""
import os
import sys
import logging
import mimetypes
import socket
from gevent import spawn, getcurrent, Timeout, GreenletExit
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, BadRequest
from msgpack import packb, Unpacker
from larch.lib.aspect import pointcut
from larch.lib.gevent import Queue
# from .session import Session, MsgDecoder
from .resource import ResourceManager


logger = logging.getLogger('larch.bo.server')
logging.getLogger("geventwebsocket.handler").setLevel(logging.ERROR)

GENTYPE = type((i for i in range(1)))


# Public Classes
# --------------
@pointcut
class ApplicationPointcut:
    def start(self, server):
        """the application is started."""

    def shutdown(self):
        """the application shutsdown."""


class MsgPacker:
    EXT_TYPES = {}

    def __init__(self):
        self.unpacker = Unpacker(raw=False, ext_hook=self._ext_hook)

    def decode(self, data):
        self.unpacker.feed(data)
        return self.unpacker.unpack()

    def _ext_hook(self, code, data):
        return self.EXT_TYPES.get(code, lambda d: d)(data)


class Application(MsgPacker):
    """The Baseclass for lui applications. Responsible for Driving the
    larch.ui.application.

    The cache functions can be subclassed to support an arbritary cache
    type.
    """
    # SESSION_FACTORY = Session
    URL_PLUGINS = {}
    pointcut = ApplicationPointcut()

    def __init__(self, config):
        super().__init__()
        config["application"] = self
        config.setdefault("max_content_length", 16*1024)
        config.setdefault("max_form_memory_size", 16*1024)

        self.config = config
        self.url_plugins = {}

        url_map = []
        for k, factory in self.URL_PLUGINS.items():
            plugin = self.url_plugins[k] = factory(config)
            setattr(self, "handle_"+k, plugin.handle_url)
            url_map.append(Rule("/_/{}/<path:path>".format(k), endpoint=k))

        if config.get("websocket", True):
            url_map += [
                Rule('/api/socket', endpoint='websocket', websocket=True),
                Rule('/api/socket', endpoint='websocket')]  # firefox

        url_map += [
            Rule('/', endpoint='resource'),
            Rule("/api/ajax/msgpack", endpoint="ajax_binary"),
            Rule('/<path:name>', endpoint='resource')]

        self.url_map = Map(url_map)
        self.api = config.get("api", object())

        for pc in config.get("application_pointcuts", []):
            pc(self)

    # startup/shutdown code
    # ---------------------
    def start(self, server):
        self.server = server
        self.pointcut.start(server)
        self.resource_manager = ResourceManager(self.config)

    def shutdown(self):
        self.resource_manager.shutdown()
        for v in self.url_plugins.values():
            v.shutdown()
        self.pointcut.shutdown()

    def __call__(self, environ, start_response):
        request = Request(environ)
        request.max_content_length = self.config["max_content_length"]
        request.max_form_memory_size = self.config["max_form_memory_size"]
        adapter = self.url_map.bind_to_environ(environ)
        try:
            try:
                endpoint, values = adapter.match()
                method = getattr(self, 'handle_' + endpoint)
                response = method(environ, request, **values)
            except Exception as e:
                logger.exception("error %r\n%r", e, environ)
                raise
        except HTTPException:
            return sys.exc_info()[1](environ, start_response)

        return response(environ, start_response)

    def handle_resource(self, environ, request, name="index.html"):
        mimetype = mimetypes.guess_type(name)[0]
        logger.debug("handle_resource %r", name)
        if request.range:
            fileobj = self.resource_manager.open_resource(name)
            return self.handle_range_request(request, fileobj, mimetype)

        result = self.resource_manager.load_resource(name)
        r = Response(result, mimetype=mimetype)
        if name != "index.html":
            r.cache_control.max_age = 604800
            r.cache_control.immutable = True
        return r

    def _test_abortion(self, sock, parent):
        if not sock.read(16):
            logger.debug("##abort ajax")
            parent.kill()

    def handle_websocket(self, environ, request):
        ws = environ.get('wsgi.websocket')
        if ws is None:
            raise BadRequest('not a websocket')

        queue_size = self.config.get("wsqueue_size", 100)
        prepare_socket(ws.stream.handler.socket)
        try:
            logger.debug("##handle socket %r", self.server)
            timeout = self.config.get("wsheartbeat", 30)
            active_requests = {}

            while True:
                with Timeout(timeout):
                    try:
                        chunk = ws.receive()
                    except Timeout:
                        ws.send_frame(b"helo", ws.OPCODE_PING)
                        continue

                obj = self.decode(chunk)
                id_ = obj["id"]
                request = active_requests.get(id_)
                if request is None:
                    if obj["action"] == "stream":
                        q = Queue(queue_size)
                        q.put(obj["data"])
                        obj["args"] = (q,)

                    obj["greenlet"] = self.server._spawn(
                        self.handle_socket_request, ws, obj, active_requests)
                    active_requests[id_] = obj
                else:
                    if request["action"] == "stream":
                        request["args"][0].put(obj["data"])
                    else:
                        request["greenlet"].kill()

            ws.close()
        except Exception as e:
            ws.close(1006)
            logger.exception("error handling websocket %r", e)
        finally:
            ws.close()

        return Response()

    def handle_socket_request(self, sock, obj, active_requests):
        compress = self.config.get("wscompress", 8192)
        try:
            result = getattr(self.api, obj["method"])(*obj["args"], **obj["kwargs"])
            for p in iter_result(result, obj)[1]:
                sock.send(p, True, len(p) >= compress)
        except GreenletExit:
            pass
        finally:
            active_requests.pop(obj["id"], None)

    def handle_ajax_binary(self, environ, request):
        logger.debug("##handle_ajax_binary\n%r", environ, stack_info=True)

        obj = self.decode(request.get_data())
        rfile = environ["wsgi.input"].rfile
        if obj["action"] == "request":
            g = spawn(self._test_abortion, rfile.raw, getcurrent())
            try:
                result = getattr(self.api, obj["method"])(*obj["args"], **obj["kwargs"])
            finally:
                g.kill()
        else:
            def reader(obj):
                yield obj["data"]
                while True:
                    chunk = rfile.read()
                    if not chunk:
                        return
                    yield self.decode(chunk)["data"]
            result = getattr(self.api, obj["method"])(*obj["args"], **obj["kwargs"])

        chunked, data = iter_result(result, obj)
        response = Response(data, mimetype="text/msgpack")
        response.direct_passthrough = chunked
        return response

    def handle_range_request(self, request, fileobj, mimetype, etag=None):
        try:
            size = fileobj.size
        except AttributeError:
            fileobj.seek(0, os.SEEK_END)
            size = fileobj.tell()

        range_ = request.range
        length = size
        start, end = range_.range_for_length(length)
        fileobj.seek(start)

        def reader():
            with fileobj:
                for i in range(start, end, 8192):
                    yield fileobj.read(min(end - i, 8192))

        r = Response(reader(), mimetype=mimetype)
        r.status_code = 206
        if etag is not None:
            r.set_etag(etag)
        r.content_length = end - start
        r.content_range = range_.make_content_range(size)
        r.accept_ranges = "bytes"
        return r


def prepare_socket(socket_):
    """
    After tests: it is faster to keep Naegle's Algorithm
    try:
        socket_.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except Exception as e:  # pragma: no cover
        logger.info("sock:Cannot set TCP_NODELAY: %r", e)
    """

    try:
        socket_.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
    except Exception as e:  # pragma: no cover
        logger.info("sock:Cannot set TCP_QUICKACK: %r", e)

    return socket_


def iter_result(result, obj):
    if isinstance(result, GENTYPE):
        def create_result():
            for r in result:
                yield packb({
                    "id": obj["id"],
                    "action": "item",
                    "item": r
                })
                logger.debug("yield item", stack_info=True)

            yield packb({
                "id": obj["id"],
                "action": "result",
                "result": None
            })
        return True, create_result()

    else:
        return False, [packb({
            "id": obj["id"],
            "action": "result",
            "result": result
            })]
