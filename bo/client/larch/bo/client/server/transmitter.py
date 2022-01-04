import time
from ..browser import create_promise, as_array

# __pragma__("skip")
console = location = Object = window = URL = Worker = None
def __pragma__(*args): pass
def __new__(a): pass
# __pragma__("noskip")


class RequestPromise:
    def __init__(self, id):
        self.id = id
        self.started = time.time()
        self._receive = self._reject = self._resolve = lambda x: None
        self.promise = create_promise(self._set_funcs)

    def then(self, *args):
        self.promise.then(*args)
        return self

    def receive(self, callback):
        self._receive = callback
        return self

    def _set_funcs(self, resolve, reject):
        self._resolve = resolve
        self._reject = reject

    def abort(self):
        window.transmitter.abort_request(self.id)

    def put(self, data):
        window.transmitter.put_more(self.id, data)


class APICall:
    def __getattr__(self, method):
        # __pragma__("kwargs")
        def wrapped_method(*args, **kwargs):
            return window.transmitter.request(method, *args, **kwargs)
        return wrapped_method


class Transmitter:
    def __init__(self, worker):
        self.worker = worker
        self.worker.onmessage = self.receive
        self.id_counter = 0
        self.active_requests = {}
        self.api = APICall()

    # __pragma__("kwargs")
    def request(self, method, *args, **kwargs):
        self.id_counter += 1
        id_ = self.id_counter
        # __pragma__("jsiter")
        obj = {
            "action": "request",
            "id": id_,
            "method": method,
            "args": as_array(args),
            "kwargs": to_jsobject(kwargs)
        }
        # __pragma__("nojsiter")
        self.worker.postMessage(obj)
        r = self.active_requests[id_] = RequestPromise(id_)
        return r
    # __pragma__("nokwargs")

    # __pragma__("kwargs")
    def put_start(self, method, data, **kwargs):
        self.id_counter += 1
        id_ = self.id_counter
        # __pragma__("jsiter")
        obj = {
            "action": "stream",
            "id": id_,
            "method": method,
            "data": data,
            "kwargs": to_jsobject(kwargs)
        }
        # __pragma__("nojsiter")
        self.worker.postMessage(obj)
        r = self.active_requests[id_] = RequestPromise(id_)
        return r
    # __pragma__("nokwargs")

    def put_more(self, id_, data):
        # __pragma__("jsiter")
        obj = {
            "action": "stream",
            "id": id_,
            "data": data
        }
        # __pragma__("nojsiter")
        self.worker.postMessage(obj)

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
                request._resolve(to_object(obj["result"]))
        elif obj["action"] == "item":
            request = self.active_requests.get(obj["id"], None)
            console.log("***received item", obj)
            if request:
                request._receive(to_object(obj["item"]))
        elif obj["action"] == "error":
            console.error("an error occured from transmission", obj)
            if obj["id"]:
                request = self.active_requests.get(obj["id"], None)
                request._reject(to_object(obj["error"]))
            else:
                error_requests = list(self.active_requests.values())
                self.active_requests.clear()
                for r in error_requests:
                    r._reject(to_object(obj))


def to_object(jsobj):
    __pragma__("js", "{}", """
    if (typeof jsobj != "object")
        return jsobj;
    """)
    result = {}
    # __pragma__("jsiter")
    for k in jsobj:
        result[k] = jsobj[k]
    # __pragma__("nojsiter")
    return result


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


def set_tmt(session):
    worker = create_worker("./socket.js")
    window.transmitter = Transmitter(worker)
    session.extern = window.transmitter.api
    session.transmitter = window.transmitter
