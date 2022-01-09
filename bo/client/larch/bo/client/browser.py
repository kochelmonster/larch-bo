from collections import deque
from larch.reactive import Reactive, Cell, rule
# __pragma__("skip")
document = window = Object = Option = None
def __pragma__(*args): pass
def __new__(p): pass
# __pragma__("noskip")


BODY = None
loading_modules = []  # to avoid controls have to reference session


__pragma__('js', '{}', '''
loading_modules.push(new Promise((resolve) => {
    document.addEventListener('DOMContentLoaded', resolve);
}));
''')


def _browser_ready(main_func):
    global BODY
    loading_modules.clear()
    BODY = document.querySelector("body")
    main_func.call()


def start_main(main_func):
    __pragma__('js', '{}', '''
        Promise.all(loading_modules).then(() => {
            _browser_ready(main_func)
        });
    ''')


def create_promise(callback):
    __pragma__('js', '{}', '''
    return new Promise(callback);
    ''')


def as_array(pyobj):
    __pragma__('js', '{}', '''
    return Array.from(pyobj);
    ''')


class LiveTracker(Reactive):
    """A Mixin for controls to watch live values"""

    def __init__(self, callback):
        self.callback = callback
        timer.start()

    @rule
    def _rule_watch_timer(self):
        timer.count
        yield
        self.callback()


class Timer(Reactive):
    TIMER_DELTA = 50   # in ms
    count = Cell(0)

    def __init__(self):
        self.started = False

    def start(self):
        if not self.started:
            __pragma__('js', '{}', '''
            setInterval(self.inc, self.TIMER_DELTA);
            ''')

    def inc(self):
        self.count += 1


timer = Timer()


class Executer:
    MAX_EXECUTON_TIME = 5   # in ms

    def __init__(self):
        self.tasks = deque()
        self.active_id = None

    def add(self, func, *args):
        self.tasks.append([func, args])
        if self.active_id is None:
            self.active_id = window.requestAnimationFrame(self._step)

    def flush(self):
        while len(self.tasks):
            task, args = self.tasks.popleft()
            task(*args)

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


def fire_event(etype, bubbles=False, cancelable=False, detail=None, element=None):
    if element is None:
        element = BODY

    __pragma__('js', '{}', '''
        var options = {
            bubbles: bubbles,
            cancelable: cancelable,
            detail: detail };
        element.dispatchEvent(new CustomEvent(etype, options));
    ''')
