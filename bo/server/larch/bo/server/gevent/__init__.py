import logging
from gevent import pywsgi

logger = logging.getLogger('larch.bo.server')
del logging


class WSGIServer(pywsgi.WSGIServer):
    def update_environ(self):
        # avoids an annoying error message in the original implementation
        logger.debug("update_environ %r", self.address)
        address = self.address
        if isinstance(address, tuple):
            self.environ.setdefault('SERVER_NAME', str(address[0]))
            self.environ.setdefault('SERVER_PORT', str(address[1]))
        else:
            self.environ.setdefault('SERVER_NAME', '')
            self.environ.setdefault('SERVER_PORT', '')


def start_wsgi(application, config):
    wsgi = config.get('wsgi', {})
    wsgi.setdefault('log', logger)

    if config.get("websocket", True):
        from .websocket import LarchWebSocketHandler
        wsgi["handler_class"] = LarchWebSocketHandler

    server = WSGIServer(config["address"], application, **wsgi)
    server.start()
    return server
