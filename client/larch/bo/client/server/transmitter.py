import time
from ..browser import as_array, PyPromise

# __pragma__("skip")
console = location = Object = window = URL = Worker = None
def __pragma__(*args): pass
def __new__(a): pass
# __pragma__("noskip")


class RequestPromise:
    def __init__(self, id):
        self.id = id
        self.started = time.time()
        self._receive = lambda x: None
        self.promise = PyPromise()

    def then(self, *args):
        self.promise.then(*args)
        return self

    def receive(self, callback):
        self._receive = callback
        return self

    def abort(self):
        window.lbo.transmitter.abort_request(self.id)

    def put(self, data):
        window.lbo.transmitter.put_more(self.id, data)


class APICall:
    def __getattr__(self, method):
        # __pragma__("kwargs")
        def wrapped_method(*args, **kwargs):
            return window.lbo.transmitter.request(method, *args, **kwargs)
        return wrapped_method


class Transmitter:
    def __init__(self, worker):
        self.worker = worker
        self.worker.onmessage = self.receive
        self.id_counter = 0
        self.active_requests = {}

    def encode(self, data):
        # __pragma__("jsiter")
        return self.send_new_message({
            "action": "encode",
            "data": data
        })
        # __pragma__("nojsiter")

    def decode(self, data):
        # __pragma__("jsiter")
        return self.send_new_message({
            "action": "decode",
            "data": data
        })
        # __pragma__("nojsiter")

    # __pragma__("kwargs")
    def request(self, method, *args, **kwargs):
        # __pragma__("jsiter")
        return self.send_new_message({
            "action": "request",
            "method": method,
            "args": as_array(args),
            "kwargs": to_jsobject(kwargs)
        })
        # __pragma__("nojsiter")

    def put_start(self, method, data, **kwargs):
        # __pragma__("jsiter")
        return self.send_new_message({
            "action": "stream",
            "method": method,
            "data": data,
            "kwargs": to_jsobject(kwargs)
        })
        # __pragma__("nojsiter")
    # __pragma__("nokwargs")

    def put_more(self, id_, data):
        # __pragma__("jsiter")
        self.worker.postMessage({
            "action": "stream",
            "id": id_,
            "data": data
        })
        # __pragma__("nojsiter")

    def send_new_message(self, obj):
        self.id_counter += 1
        id_ = self.id_counter
        obj.id = id_
        self.worker.postMessage(obj)
        r = self.active_requests[id_] = RequestPromise(id_)
        return r

    def abort_request(self, id_):
        request = self.active_requests.pop(id_, None)
        if request is not None:
            __pragma__("ifdef", "verbose1")
            console.log("abort request", request)
            __pragma__("endif")
            self.worker.postMessage({
                "action": "cancel",
                "id": id_
            })

    def receive(self, event):
        obj = event.data
        if obj["action"] == "result":
            request = self.active_requests.pop(obj["id"], None)
            if request:
                request.promise.resolve(obj["result"])
        elif obj["action"] == "item":
            request = self.active_requests.get(obj["id"], None)
            if request:
                request._receive(obj["item"])
        elif obj["action"] == "error":
            console.warn("an error occured from transmission", obj)
            if obj["id"]:
                request = self.active_requests.get(obj["id"], None)
                request.promise.reject(obj["error"])
            else:
                error_requests = list(self.active_requests.values())
                self.active_requests.clear()
                for r in error_requests:
                    r.promise.reject(obj)


def to_jsobject(pyobj):
    result = {}  # __:jsiter
    for k, v in pyobj.items():
        result[k] = v
    return result


def create_worker(url):
    if (location.protocol == "file:"):
        tmp = __new__(URL(location.href))
        url += "?transmitter=" + tmp.searchParams.get("transmitter")

    __pragma__("jsiter")
    __pragma__("ifdef", "classic")
    return __new__(Worker(url, {"type": "classic"}))
    __pragma__("else")
    return __new__(Worker(url, {"type": "module"}))
    __pragma__("endif")
    __pragma__("nojsiter")


window.lbo.transmitter = Transmitter(create_worker("./socket.js"))
window.lbo.server = APICall()
