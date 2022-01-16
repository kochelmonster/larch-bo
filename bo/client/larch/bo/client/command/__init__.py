from .. import browser  # for window.lbo

# __pragma__("skip")
browser
window = document = js_undefined = console = String = setInterval = clearInterval = None
def require(p): pass
# __pragma__("noskip")
# __pragma__("ecom")


require("./larch.bo.command.scss")


def label(prop):
    def wrapped(func):
        func.__label__ = prop
        return func
    return wrapped


def icon(prop):
    def wrapped(func):
        func.__icon__ = prop
        return func
    return wrapped


def ricon(prop):
    def wrapped(func):
        func.__ricon__ = prop
        return func
    return wrapped


def tooltip(prop):
    def wrapped(func):
        func.__tooltip__ = prop
        return func
    return wrapped


# __pragma__("kwargs")
def command(global_=False, id_=None, key=None, label=None, icon=None, tooltip=None):
    # __pragma__("nokwargs")
    def wrapped(func):
        func.__command__ = id_ or True
        if global_:
            func.__command_is_global__ = True
        if key:
            func.__key__ = key
        if label:
            func.__label__ = label
        if icon:
            func.__icon__ = icon
        if tooltip:
            func.tooltip = tooltip
        return func
    return wrapped


def get_func_prop(func, id_):
    result = func[id_]
    return None if result is js_undefined else result


def stop_event(event):
    event.stopPropagation()
    event.preventDefault()


class CommandHandler:
    """Mixin for Control to handle commands and key strokes"""

    def collect_commands(self, element):
        """collect the commands and registeres them in element"""
        commands = {}  # __:jsiter
        functype = type(stop_event)
        is_global = False
        for name in dir(self):
            v = getattr(self, name)
            if isinstance(v, functype):
                command = v.__command__
                if command:
                    if command is True:
                        command = name.replace("_", "-")
                    commands[command] = v
                if v.__command_is_global__:
                    is_global = True

        if len(commands):
            make_command_manager()
            element.lbo_commands = commands
            if is_global:
                element.classList.add("lbo-commands")

    def enable_command(self, name, enabled):
        """Enables or disables a command"""
        pass

    def render(self, parent):
        super().render(parent)
        self.collect_commands(parent.firstChild)


class CommandManager:
    # __pragma__("jsiter")
    SPECIAL_KEYS = {
        8: "backspace", 9: "tab", 13: "return", 16: "shift", 17: "ctrl",
        18: "alt", 19: "pause", 20: "capslock", 27: "esc", 32: "space",
        33: "pageup", 34: "pagedown", 35: "end", 36: "home", 37: "left",
        38: "up", 39: "right", 40: "down", 45: "insert", 46: "del", 96: "0",
        97: "1", 98: "2", 99: "3", 100: "4", 101: "5", 102: "6", 103: "7",
        104: "8", 105: "9", 106: "*", 107: "+", 109: "-", 110: ".",
        111: "/", 112: "f1", 113: "f2", 114: "f3", 115: "f4", 116: "f5",
        117: "f6", 118: "f7", 119: "f8", 120: "f9", 121: "f10", 122: "f11",
        123: "f12", 144: "numlock", 145: "scroll", 186: ";", 191: "/",
        220: "\\", 222: "'", 224: "meta", 187: "+", 189: "-", 171: "+",
        173: "-"}

    TAP_EVENTS = {"tapstart": True}

    IGNOREKEYS = {"shift": True, "alt": True, "ctrl": True}

    SHIFTNUMS = {
        "`": "~", "1": "!", "2": "@", "3": "#", "4": "$", "5": "%",
        "6": "^", "7": "&", "8": "*", "9": "(", "0": ")", "-": "_",
        "=": "+", ";": ": ", "'": "\"", ",": "<", ".": ">", "/": "?",
        "\\": "|"}

    EVENTS = ["keydown", "click", "dblclick", "mousedown", "mouseup", "wheel"]
    # __pragma__("nojsiter")

    KEY_ABORT = "ctrl+g"

    LONG_CLICK_DELAY = 520  # ms

    click_start_time = None  # for long click
    active_key_sequence = ""

    def __init__(self):
        for e in self.EVENTS:
            document.addEventListener(e, self.on_event)
        self.keystroke_div = self.create_keystroke_div()
        self.keystroke_div.classList.add("hidden")
        document.body.appendChild(self.keystroke_div)

    def create_keystroke_div(self):
        el = document.createElement("div")
        el.id = "lbo-keystrokes"
        return el

    def on_event(self, event):
        detected_keys = self.event_to_key(event)
        if detected_keys:
            self.match_command(event, detected_keys)

    def start_key_sequence(self, key):
        self.active_key_sequence = key + " "
        self.show_keys(key.split(" "))

    def show_keys(self, keys):
        self.keystroke_div.innerHTML = ""
        for k in keys:
            el = document.createElement("span")
            el.classList.add("lbo-keystroke")
            el.innerText = k
            self.keystroke_div.appendChild(el)
        self.keystroke_div.classList.remove("hidden")

    def stop_key_sequence(self):
        self.active_key_sequence = ""
        self.keystroke_div.classList.add("hidden")

    def match_command(self, event, detected_keys):
        for element in event.path:
            if element.lbo_commands:
                if self.execute_command(element, event, detected_keys, 0):
                    return

        for element in document.querySelectorAll(".lbo-commands"):
            if element.lbo_commands:
                if self.execute_command(element, event, detected_keys, 1):
                    return

        self.stop_key_sequence()

    def execute_command(self, element, event, detected_keys, only_globals):
        # __pragma__("jsiter")
        for c in element.lbo_commands:
            # __pragma__("nojsiter")
            func = element.lbo_commands[c]
            if int(bool(func.__command_is_global__)) < only_globals:
                continue

            for command_key in (func.__key__ or "").split(","):
                # __pragma__("jsiter")
                for dk in detected_keys:
                    # __pragma__("nojsiter")
                    if command_key.startswith(dk):
                        if command_key == dk:
                            self.stop_key_sequence()
                            window.lbo.command_context = {"event": event}  # __:jsiter
                            if func() is not False:
                                stop_event(event)
                            window.lbo.command_context = None
                            return True
                        else:
                            # a key sequence
                            self.start_key_sequence(dk)
                            stop_event(event)
                            return True

    def event_to_key(self, event):
        # translates an event to the appropriate key sequences

        etype = event["type"]
        if self.TAP_EVENTS[etype]:
            return {etype: True}  # __:jsiter

        # Keypress represents characters, not special keys
        special = etype != "keypress" and self.SPECIAL_KEYS[event.which]
        character = String.fromCharCode(event.which).toLowerCase()
        modif = ""

        if self.IGNOREKEYS[special]:
            self.stop_key_sequence()
            return None

        # check combinations (alt|ctrl|shift+anything)
        if event.altKey:
            modif += "alt+"
        if event.ctrlKey:
            modif += "ctrl+"

        # TODO: Need to make sure this works consistently across platforms
        if event.metaKey and not event.ctrlKey and special != "meta":
            modif += "meta+"

        if not self.active_key_sequence and etype.startswith("key") and not modif and not special:
            # ignore normal input typing
            self.stop_key_sequence()
            return None

        if event.shiftKey and special != "shift":
            modif += "shift+"

        if etype == "wheel":
            direction = "up" if event.deltaY > 0 else "down"
            return {modif+"mousewheel-"+direction: True}  # __:jsiter

        if event.button != js_undefined:
            if etype == "contextmenu":
                return {self.active_key_sequence+"contextmenu": True}  # __:jsiter

            if etype == "mousedown":
                self.click_start_time = window.performance.now()

            # mouse
            if etype == "click":
                if window.performance.now() - self.click_start_time >= self.LONG_CLICK_DELAY:
                    etype = "longclick"

            return {self.active_key_sequence+modif+etype+"-"+event.button: True}  # __:jsiter

        if special:
            return {self.active_key_sequence+modif+special: True}  # __:jsiter

        detected_keys = {}  # __:jsiter
        detected_keys[self.active_key_sequence+modif+character] = True
        shifted = self.SHIFTNUMS[character]
        if shifted:
            detected_keys[self.active_key_sequence+modif+shifted] = True
            # "$" can be triggered as "Shift+4" or "Shift+$" or just "$"
            if modif == "shift+":
                detected_keys[self.active_key_sequence+shifted] = True

        return detected_keys


def make_command_manager():
    if not window.lbo.commands:
        window.lbo.commands = CommandManager()
