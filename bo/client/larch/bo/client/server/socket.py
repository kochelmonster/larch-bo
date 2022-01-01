from .endecode import DecoderPipe, EncoderPipe, as_js_object, get_api_baseurl
# __pragma__("skip")
self = None
def create_websocket(u): pass
def __pragma__(*args): pass
def postMessage(data): pass
def setTimeout(func, delta): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
self.onmessage = function(e) {
    socket.send(e.data)
}

function create_websocket(url) {
    return new WebSocket(url);
}
''')


url = get_api_baseurl() + "/api/socket"
url = url.replace("http://", "ws://").replace("https://", "wss://")


class Socket:
    def __init__(self):
        self.encoder = EncoderPipe(self.transmit)
        self.decoder = DecoderPipe(lambda d: postMessage(d))
        self.start_socket()

    def receive(self, event):
        self.decoder.write(event.data)

    def send(self, obj):
        self.encoder.write(obj)

    def transmit(self, data):
        self.websocket.send(data)

    def start_socket(self):
        self.websocket = ws = create_websocket(url)
        ws.binaryType = "arraybuffer"
        ws.onmessage = self.receive
        ws.onerror = self.inform_error

    def inform_error(self, event):
        postMessage(as_js_object({
            "action": "result",
            "error": as_js_object({
                "closed": self.websocket.readyState == 3
            })
        }))
        setTimeout(self.start_socket, 500)


socket = Socket()
