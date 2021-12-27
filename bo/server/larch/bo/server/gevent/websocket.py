from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.websocket import WebSocket


class LarchWebSocketHandler(WebSocketHandler):
    websocket_class = WebSocket

    def get_environ(self):
        environ = super().get_environ()
        if not self.server.application.config.get("compress_socket", True):
            environ.pop("HTTP_SEC_WEBSOCKET_EXTENSIONS", None)
        return environ
