"""Provides an Application object as base for specfic larch.ui Applications."""
import os
import sys
import logging
import mimetypes
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, BadRequest, NotFound
from user_agents import parse
from larch.lib.aspect import pointcut, aspect
# from .session import Session, MsgDecoder
from .resource import ResourceManager


logger = logging.getLogger('larch.ui')
logging.getLogger("geventwebsocket.handler").setLevel(logging.ERROR)


# Public Classes
# --------------
@pointcut
class ApplicationPointcut:
    def start(self, server):
        """the application is started."""

    def shutdown(self):
        """the application shutsdown."""

    def session_from_cache(self, session):
        """session was recreated from cache"""

    def new_session(self, session):
        """a new session was created"""

    def remove_session(self, session):
        """before a session is destroyed"""

    def lost_socket(self, session):
        """session lost socket."""

    def got_socket(self, session):
        """session got socket."""

    def start_task_exec(self, session, func, args, kwargs):
        """a session starts executing a task"""

    def end_task_exec(self, session, func, args, kwargs):
        """a session starts executing a task"""

    def before_quit(self, session):
        """is called by window before the application quits"""

    def session_painted(self, session):
        """is called after session.repaint was called"""


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
                Rule('/ws/<path:kind>', endpoint='websocket', websocket=True),
                Rule('/ws/<path:kind>', endpoint='websocket')]  # firefox

        url_map += [
            Rule('/', endpoint='resource'),
            Rule('/<path:name>', endpoint='resource')]

        self.url_map = Map(url_map)

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

    def handle_websocket(self, environ, request, kind):
        ws = environ.get('wsgi.websocket')
        if ws is None:
            raise BadRequest('not a websocket')

        try:
            decoder = MsgDecoder(ws)
            request = decoder.get()
            session = self.make_session(request)
            session.start_websocket(decoder, request, environ)
            ws.close()
        except StopIteration:
            pass
        except Exception as e:
            ws.close(1006)
            logger.exception("error handling websocket %r", e)
        finally:
            ws.close()

        return Response()

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

    def lost_socket(self, session):
        self.pointcut.lost_socket(session)

    def got_socket(self, session):
        self.pointcut.got_socket(session)
