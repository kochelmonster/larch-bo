# __pragma__("skip")
class Mock:
    protocol = origin = ""


console = Object = location = Mock()
def create_websocket(u): pass
def __pragma__(*args): pass
def postMessage(data): pass
def setTimeout(func, delta): pass
def require(p): pass
def create_array(): pass
def feed(d): pass
def create_decoder(d): pass

# __pragma__("noskip")


msgpack = require("msgpack-lite/dist/msgpack.min.js")


__pragma__('js', '{}', '''
self.onmessage = function(e) {
    var request = e.data;
    switch(request.action) {
     case "encode":
        request.action = "result";
        request.result = msgpack.encode(request.data);
        delete request.data
        postMessage(request);
        return;

     case "decode":
         try {
            request.result = msgpack.decode(request.data);
            request.action = "result";
         } catch (exc) {
            request.action = "error";
            request.error = exc.toString();
            request["from"] = "decode"
         }
         delete request.data
         postMessage(request);
         return;
    }
    send_request(request);
}

function create_websocket(url) {
    return new WebSocket(url);
}

function create_array() {
    return [];
}

function create_decoder(callback) {
    var codec = msgpack.createCodec({preset: true, safe: false});
    var decoder = msgpack.Decoder({codec: codec});
    decoder.push = callback;
    return decoder;
}

function feed(data) {
    decoder.write(new Uint8Array(data));
    decoder.flush();
}
''')


def obj_receive(obj):
    postMessage(obj)


decoder = create_decoder(obj_receive)


def get_api_baseurl():
    if location.protocol == "file:":
        __pragma__('js', '{}', '''
        url = new URL(location.href);
        return "http://localhost:"+url.searchParams.get("transmitter");
        ''')
    else:
        return location.origin


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
        p = msgpack.encode(request)
        # console.log("send request", request, p.length)
        active_socket.send(p)
        # active_socket.send(msgpack.encode(request))


def wsopen(event):
    global waiting_requests
    if waiting_requests:
        # console.log("open socket", waiting_requests)
        for r in waiting_requests:
            active_socket.send(msgpack.encode(r))
        waiting_requests = None


def wsreceive(event):
    feed(event.data)


def wserror(event):
    global active_socket
    console.warn("got websocket error", event, active_socket)
    # __pragma__("jsiter")
    postMessage({
        "action": "error",
        "error": {
            "msg": "socket closed",
            "state": active_socket.readyState == 3
        }
    })
    # __pragma__("nojsiter")
    active_socket.close()
    active_socket = None
