import time
from ..browser import create_promise, as_array

# __pragma__("skip")
location = Object = window = None
def __pragma__(*args): pass
# __pragma__("noskip")


def as_js_object(dict_):
    obj = Object.create(None)
    for k, v in dict_.items():
        obj[k] = v
    return obj


class RequestPromise:
    def __init__(self, id):
        self.id = id
        self.started = time.time()
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
        obj = as_js_object({
            "action": "request",
            "id": id_,
            "method": method,
            "args": as_array(args),
            "kwargs": as_js_object(kwargs)
        })
        self.worker.postMessage(obj)
        r = self.active_requests[id_] = RequestPromise(id_)
        return r
    # __pragma__("nokwargs")

    def put_start(self, method, data):
        self.id_counter += 1
        id_ = self.id_counter
        obj = as_js_object({
            "action": "stream",
            "id": id_,
            "method": method,
            "data": data
        })
        self.worker.postMessage(obj)
        r = self.active_requests[id_] = RequestPromise(id_)
        return r

    def put_more(self, id_, data):
        obj = as_js_object({
            "action": "stream",
            "id": id_,
            "data": data
        })
        self.worker.postMessage(obj)

    def abort_request(self, id_):
        request = self.active_requests.pop(id_, None)
        if request is not None:
            self.worker.postMessage({
                "action": "cancel",
                "id": id_
            })

    def receive(self, event):
        obj = event.data
        if obj["action"] == "result":
            request = self.active_requests.pop(obj["id"], None)
            if request:
                if obj["error"]:
                    print("error in transmission", obj)
                    request._reject(obj["error"])
                else:
                    request._resolve(obj["result"])
        elif obj["action"] == "item":
            request = self.active_requests.get(obj["id"], None)
            if request:
                request._receive(obj["item"])


def create_worker(url):
    __pragma__('js', '{}', '''
    if (location.protocol == "file:") {
        var tmp = new URL(location.href);
        url += "?transmitter=" + tmp.searchParams.get("transmitter");
    }
    return new Worker(url, {type: "classic"});
    ''')


def set_tmt(session):
    __pragma__("ifdef", "ajax")
    worker = create_worker("./ajax.js")
    __pragma__("else")
    worker = create_worker("./socket.js")
    __pragma__("endif")

    window.transmitter = Transmitter(worker)
    session.extern = window.transmitter.api
