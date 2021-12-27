from .endecode import DecoderPipe, EncoderPipe, as_js_object


# __pragma__("skip")
class Mock:
    origin = ""


location = Mock()
def create_ajax(): pass
def __pragma__(*args): pass
def postMessage(data): pass
# __pragma__("noskip")


last_id = None
active_requests = {}


__pragma__('js', '{}', '''
self.onmessage = function(e) {
    transmit(e.data)
}

function create_ajax() {
    return new XMLHttpRequest();
}
''')

url = location.origin + "/api/ajax/msgpack"


def transmit(obj):
    global last_id

    if (obj["action"] == "cancel"):
        request = active_requests.pop(obj["id"], None)
        if request is not None:
            request.abort()
        return

    last_id = obj["id"]
    encoder.write(obj)


def send(data):
    id_ = last_id

    def load():
        if request.status != 200:
            error()
            return
        decoder.write(request.response)

    def error():
        active_requests.pop(id_, None)
        postMessage(as_js_object({
            "id": id_,
            "action": "result",
            "error": as_js_object({
                "source": "client",
                "status": request.status,
                "text": request.statusText
                })}))

    request = active_requests.get(id_)
    if request is None:
        request = create_ajax()
        request.open("post", url)
        request.responseType = "arraybuffer"
        request.onload = load
        request.onerror = error
        active_requests[id_] = request
        # xhr.setRequestHeader("Transfer-Encoding", "chunked");

    request.send(data)


def receive(result):
    if result.action != "item":
        active_requests.pop(result.id, None)
    postMessage(result)


decoder = DecoderPipe(receive)
encoder = EncoderPipe(send)
