# __pragma__("skip")
class Mock:
    protocol = origin = ""


Object = location = Mock()
def create_websocket(u): pass
def __pragma__(*args): pass
def postMessage(data): pass
def setTimeout(func, delta): pass
def require(p): pass
def create_array(): pass
def decode(d): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
self.onmessage = function(e) {
    send_request(e.data);
}

function create_websocket(url) {
    return new WebSocket(url);
}

function create_array() {
    return [];
}

function decode(buffer) {
    return msgpack.decode(new Uint8Array(buffer));
}
''')


def get_api_baseurl():
    if location.protocol == "file:":
        __pragma__('js', '{}', '''
        url = new URL(location.href);
        return "http://localhost:"+url.searchParams.get("transmitter");
        ''')
    else:
        return location.origin


def as_js_object(dict_):
    obj = Object.create(None)
    for k, v in dict_.items():
        obj[k] = v
    return obj


msgpack = require("msgpack-lite")

url = get_api_baseurl() + "/api/socket"
url = url.replace("http://", "ws://").replace("https://", "wss://")


waiting_requests = None
active_socket = None


def send_request(request):
    global waiting_requests
    global active_socket

    if not active_socket or active_socket.readyState != 1:
        if not waiting_requests:
            waiting_requests = create_array()

        waiting_requests.push(request)

        if not active_socket or active_socket.readyState >= 2:
            active_socket = create_websocket(url)
            active_socket.binaryType = "arraybuffer"
            active_socket.onopen = wsopen
            active_socket.onmessage = wsreceive
            active_socket.onerror = wserror
    else:
        active_socket.send(msgpack.encode(request))


def wsopen(event):
    global waiting_requests
    if waiting_requests:
        for r in waiting_requests:
            active_socket.send(msgpack.encode(r))
        waiting_requests = None


def wsreceive(event):
    postMessage(decode(event.data))


def wserror(event):
    postMessage(as_js_object({
        "action": "error",
        "error": as_js_object({
            "closed": active_socket.readyState == 3
        })
    }))
