"""Provides an Application object as base for specfic larch.ui Applications."""
import os
import sys
import logging
import mimetypes
import socket
from time import time
from datetime import datetime, date, time as dtime
from gevent import Timeout, GreenletExit
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, BadRequest
from msgpack import packb, ExtType, Unpacker
from larch.lib.aspect import pointcut
from larch.lib.gevent import Queue
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


class MsgDecoder:
    EXT_TYPES = {}

    def __init__(self):
        self.unpacker = Unpacker(raw=False, strict_map_key=False, ext_hook=self._ext_hook)

    def decode(self, data):
        self.unpacker.feed(data)
        return self.unpacker

    def _ext_hook(self, code, data):
        return self.EXT_TYPES.get(code, lambda d: d)(data)


def convert_to_msgpack(obj):
    """some standard conversions"""

    if isinstance(obj, datetime):
        return ExtType(0x0D, packb(int(obj.timestamp()*1000)))

    if isinstance(obj, date):
        return ExtType(0x0D, packb(int(datetime.combine(obj, dtime()).timestamp()*1000)))

    raise TypeError("cannot convert type to msgpck", type(obj), obj)


class Application:
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

    def handle_websocket(self, environ, request):
        ws = environ.get('wsgi.websocket')
        if ws is None:
            raise BadRequest('not a websocket')

        prepare_socket(ws.stream.handler.socket)
        try:
            logger.debug("##handle socket %r", self.server)
            queue_size = self.config.get("wsqueue_size", 100)
            heartbeat = self.config.get("wsheartbeat", 30)
            max_inactive_time = self.config.get("wsmax_inactive_time", 360000)  # vrtually never

            active_requests = {}
            last_active = time()
            decode = MsgDecoder().decode

            while True:
                with Timeout(heartbeat):
                    try:
                        chunk = ws.receive()
                        if chunk is None:
                            break
                    except Timeout:
                        if time() - last_active > max_inactive_time and not active_requests:
                            break
                        ws.send_frame(b"helo", ws.OPCODE_PING)
                        continue

                last_active = time()
                for obj in decode(chunk):
                    logger.debug("received request %r\n%r", obj["id"], obj)
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
                        if obj["action"] == "stream":
                            request["args"][0].put(obj["data"])
                        else:
                            logger.debug("##kill worker\n%r\n%r", request, obj)
                            request["greenlet"].kill()
        except Exception as e:
            ws.close(1006)
            logger.exception("error handling websocket %r", e)
        finally:
            ws.close()

        return Response()

    def handle_socket_request(self, sock, obj, active_requests):
        compress = self.config.get("wscompress", 8192)
        try:
            if obj["method"].startswith("_"):
                raise RuntimeError("not allowed", obj["method"])

            result = getattr(self.api, obj["method"])(*obj["args"], **obj["kwargs"])
            for o in iter_result(result, obj)[1]:
                p = packb(o, default=convert_to_msgpack)
                logger.debug("send response %r\n%r", len(p), o)
                sock.send(p, True, len(p) >= compress)
        except Exception as e:
            logger.exception("exception executing %r\n%r", e, obj)
            p = packb({"action": "error", "id": obj["id"], "error": {"msg": repr(e)}})
            sock.send(p, True, len(p) >= compress)
        except GreenletExit:
            pass
        finally:
            active_requests.pop(obj["id"], None)

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
                yield {
                    "id": obj["id"],
                    "action": "item",
                    "item": r}

            yield {
                "id": obj["id"],
                "action": "result",
                "result": None
            }
        return True, create_result()

    else:
        return False, [{
            "id": obj["id"],
            "action": "result",
            "result": result
            }]
