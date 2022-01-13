from collections import deque
# __pragma__("skip")
document = window = Object = Option = Promise = None
def __pragma__(*args): pass
def __new__(p): pass
# __pragma__("noskip")


loading_modules = []  # to avoid controls have to reference session

__pragma__('js', '{}', '''
window.lbo = {}   // globals for larch browser objects

loading_modules.push(new Promise((resolve) => {
    document.addEventListener('DOMContentLoaded', resolve);
}));
''')


def get_info():
    __pragma__('js', '{}', '''
var
    ua = navigator.userAgent,
    browser = /Edge\/\d+/.test(ua) ? 'ed' : /MSIE 9/.test(ua) ? 'ie9' : /MSIE 10/.test(ua) ? 'ie10' : /MSIE 11/.test(ua) ? 'ie11' : /MSIE\s\d/.test(ua) ? 'ie?' : /rv\:11/.test(ua) ? 'ie11' : /Firefox\W\d/.test(ua) ? 'ff' : /Chrome\W\d/.test(ua) ? 'gc' : /Chromium\W\d/.test(ua) ? 'oc' : /\bSafari\W\d/.test(ua) ? 'sa' : /\bOpera\W\d/.test(ua) ? 'op' : /\bOPR\W\d/i.test(ua) ? 'op' : typeof MSPointerEvent !== 'undefined' ? 'ie?' : '',
    os = /Windows NT 10/.test(ua) ? "win10" : /Windows NT 6\.0/.test(ua) ? "winvista" : /Windows NT 6\.1/.test(ua) ? "win7" : /Windows NT 6\.\d/.test(ua) ? "win8" : /Windows NT 5\.1/.test(ua) ? "winxp" : /Windows NT [1-5]\./.test(ua) ? "winnt" : /Mac/.test(ua) ? "mac" : /Linux/.test(ua) ? "linux" : /X11/.test(ua) ? "nix" : "",
    mobile = /IEMobile|Windows Phone|Lumia/i.test(ua) ? 'w' : /iPhone|iP[oa]d/.test(ua) ? 'i' : /Android/.test(ua) ? 'a' : /BlackBerry|PlayBook|BB10/.test(ua) ? 'b' : /Mobile Safari/.test(ua) ? 's' : /webOS|Mobile|Tablet|Opera Mini|\bCrMo\/|Opera Mobi/i.test(ua) ? 1 : 0,
    tablet = /Tablet|iPad/i.test(ua),
    touch = 'ontouchstart' in document.documentElement;

    return {
        browser: browser,
        os: os,
        mobile: mobile,
        tablet: tablet,
        touch: touch
    };
''')
    return {"browser": "win10", "mobile": False, "tablet": False, "touch": False}  # __:skip


def _browser_ready(main_func):
    loading_modules.clear()
    main_func.call()


def start_main(main_func):
    __pragma__('js', '{}', '''
        Promise.all(loading_modules).then(() => {
            _browser_ready(main_func)
        });
    ''')


def as_array(pyobj):
    __pragma__('js', '{}', '''
    return Array.from(pyobj);
    ''')


class Executer:
    MAX_EXECUTON_TIME = 5   # in ms

    def __init__(self):
        self.tasks = deque()
        self.active_id = None

    def add(self, func, *args):
        self.tasks.append([func, args])
        if self.active_id is None:
            self.active_id = window.requestAnimationFrame(self._step)
        return self

    def flush(self):
        while len(self.tasks):
            task, args = self.tasks.popleft()
            task(*args)
        return self

    def _step(self, call_time):
        while len(self.tasks):
            task, args = self.tasks.popleft()
            task(*args)

            if window.performance.now() - call_time > self.MAX_EXECUTION_TIME:
                self.active_id = window.requestAnimationFrame(self._step)
                return
        self.active_id = None


executer = Executer()


def get_bubble_attribute(element, attribute, default):
    while element:
        if element[attribute]:
            return element[attribute]
        element = element.parentElement
    return default


icons = {}


def register_icon(name, icon):
    icons[name] = icon


def get_icon(name):
    return icons.get(name, name)


def element_from_html(html):
    tmp = document.createElement("div")
    tmp.innerHTML = html
    return tmp.firstChild


def remove_slot(element, slot_name):
    part = element.querySelector(f"[slot={slot_name}]")
    if part:
        part.remove()


def add_slot(element, slot_name, slot_obj):
    if isinstance(slot_obj, str):
        slot_obj = element_from_html(slot_obj)
    if slot_name:
        slot_obj.slot = slot_name
    element.appendChild(slot_obj)


def escape(text):
    return __new__(Option(text)).innerHTML


def fire_event(etype, element=None, detail=None, bubbles=False, cancelable=False):
    if element is None:
        element = document

    __pragma__('js', '{}', '''
        var options = {
            bubbles: bubbles,
            cancelable: cancelable,
            detail: detail };
        element.dispatchEvent(new CustomEvent(etype, options));
    ''')


metrics = None


def get_metrics():
    global metrics

    if metrics is None:
        metrics = {}  # __:jsiter
        tmp = document.createElement("div")
        tmp.style.display = "inline-block"
        tmp.position = "absolute"
        tmp.visibility = "hidden"
        tmp["font-family"] = "Courier New"
        document.body.appendChild(tmp)
        rect = tmp.getBoundingClientRect()
        metrics.line_height = rect.height
        metrics.ex_width = rect.width
        tmp.innerHTML = "&mdash;"
        metrics.em_width = tmp.getBoundingClientRect().width
        tmp.style.height = "1pt"
        metrics.pt_height = tmp.getBoundingClientRect().height
        tmp.remove()

    return metrics


class PyPromise:
    def __init__(self):
        self.promise = __new__(Promise(self.set_handlers))

    def set_handlers(self, resolve, reject):
        self.resolve = resolve
        self.reject = reject

    def then(self, resolve, reject):
        self.promise.then(resolve, reject)
        return self
