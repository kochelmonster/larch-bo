from gevent import event
from geventwebsocket.handler import WebSocketHandler
from geventwebsocket.websocket import WebSocket


class PongWebSocket(WebSocket):
    """a websocket that handles pongs"""
    __slots__ = WebSocket.__slots__ + ("pong_result",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pong_result = event.AsyncResult()

    def handle_pong(self, header, payload):
        self.pong_result.set(payload)


class LarchWebSocketHandler(WebSocketHandler):
    websocket_class = PongWebSocket

    def get_environ(self):
        environ = super().get_environ()
        if not self.server.application.config.get("compress_socket", True):
            environ.pop("HTTP_SEC_WEBSOCKET_EXTENSIONS", None)
        return environ
