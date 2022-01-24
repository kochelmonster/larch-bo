from . import command, stop_event, MixinCommandHandler
from ..i18n import pgettext
# __pragma__("skip")
window = document = console = setInterval = clearInterval = None
def require(p): pass
# __pragma__("noskip")


def common_prefix(s1, s2):
    for i, (c1, c2) in enumerate(zip(s1, s2)):
        if c1 != c2:
            return i
    return i + 1


class MiniBuffer(MixinCommandHandler):
    """Enter commands from a minibuffer line like emacs"""
    TIMER_DELTA = 50

    def __init__(self):
        self.current_target = None
        self.active_commands = {}   # __:jsiter
        self.history = []
        self.history_cursor = 0
        self.minibuffer_div = self.create_minibuffer_div()
        self.input = self.minibuffer_div.querySelector("input")
        self.input.addEventListener("blur", self.on_blur)
        self.choice_div = self.create_command_choice_dev()
        self.choice_div.addEventListener("click", self.on_command_clicked)

    @command(global_=True, key="alt+x")
    def _show_minibuffer(self):
        event = window.lbo.command_context.event
        self.history_cursor = len(self.history)
        self.current_target = event.target
        self.collect_minibuffer_commands(event)
        self.minibuffer_div.classList.remove("hidden")
        self.old_value = self.input.value = ""
        self.input.focus()
        self.timer_id = setInterval(self._poll, self.TIMER_DELTA)

    @command(key="return")
    def _execute(self):
        func = self.active_commands[self.input.value]
        if func:
            try:
                self.history.remove(self.input.value)
            except ValueError:
                pass
            self.history.append(self.input.value)
            window.lbo.command_context = {"minibuffer": True}  # __:jsiter
            func()
            window.lbo.command_context = None
            self._hide_minibuffer()

    @command(key="ctrl+g")
    def _hide_minibuffer(self):
        self.minibuffer_div.classList.add("hidden")
        self.choice_div.classList.add("hidden")
        if self.current_target:
            self.current_target.focus()
            self.current_target = None
        clearInterval(self.timer_id)

    @command(key="tab")
    def _show_completion(self):
        self.update_choice(self.input.value)
        if self.choice_div.childElementCount:
            self.choice_div.classList.remove("hidden")

            self.complete_input()
        else:
            self.choice_div.classList.add("hidden")

    @command(key="left")
    def _move_left(self, event):
        if self.input.selectionStart > 0:
            return False

        self.history_cursor = max(self.history_cursor - 1, 0)
        if self.history.length:
            self.input.value = self.history[self.history_cursor]

        self.input.selectionStart = self.input.selectionEnd = 0
        return False

    @command(key="right")
    def _move_right(self, event):
        value = self.input.value
        if self.input.selectionStart < len(value):
            return False

        self.history_cursor = min(self.history_cursor + 1, len(self.history))
        if self.history_cursor < len(self.history):
            self.input.value = self.history[self.history_cursor]
        else:
            self.input.value = ""

        self.input.selectionStart = self.input.selectionEnd = len(self.input.value)
        return False

    def complete_input(self):
        prefix = 100000
        before = self.choice_div.firstChild.innerText
        for c in self.choice_div.children:
            command = c.innerText
            prefix = min(common_prefix(before, command), prefix)
            before = command
        self.input.value = command[:prefix]

    def create_minibuffer_div(self):
        div = document.createElement("div")
        div.classList.add("hidden")
        div.id = "lbo-minibuffer"
        label = document.createElement("label")
        label.innerText = str(pgettext("minibuffer", "Command"))
        div.appendChild(label)
        input_ = document.createElement("input")
        div.appendChild(input_)
        return div

    def create_command_choice_dev(self):
        div = document.createElement("div")
        div.id = "lbo-minibuffer-choice"
        div.classList.add("hidden")
        return div

    def render(self, parent):
        parent.appendChild(self.minibuffer_div)
        parent.appendChild(self.choice_div)
        self.collect_commands(self.minibuffer_div)
        return self

    def _poll(self):
        value = self.input.value
        if value != self.old_value and not self.choice_div.classList.contains("hidden"):
            self.old_value = value
            self.update_choice(value)

    def update_choice(self, value):
        self.choice_div.innerHTML = ""
        # __pragma__("jsiter")
        commands = [id_ for id_ in self.active_commands if id_.startswith(value)]
        # __pragma__("nojsiter")

        if command.length:
            self.choice_div.classList.remove("hidden")
        else:
            self.choice_div.classList.add("hidden")
            return

        commands.sort()
        self.choice_div.style["grid-template-columns"] = ""
        self.choice_div.style.width = ""
        for id_ in commands:
            element = document.createElement("div")
            element.tabIndex = "-1"
            element.command = id_
            element.innerText = id_
            self.choice_div.appendChild(element)

        width = self.choice_div.getBoundingClientRect().width
        self.choice_div.style.width = "100%"
        self.choice_div.style["grid-template-columns"] = f"repeat(auto-fit, {width}px)"

        irect = self.minibuffer_div.getBoundingClientRect()
        crect = self.choice_div.getBoundingClientRect()
        self.choice_div.style.top = irect.top - crect.height + "px"

    def collect_minibuffer_commands(self, event):
        self.active_commands = {}   # __:jsiter

        for element in document.querySelectorAll(".lbo-commands"):
            self.collect_commands_from_element(element, self.active_commands, 1)

        for element in event.composedPath():
            self.collect_commands_from_element(element, self.active_commands, 0)

    def collect_commands_from_element(self, element, result, only_globals):
        if element.lbo_commands:
            # __pragma__("jsiter")
            for id_ in element.lbo_commands:
                # __pragma__("nojsiter")
                if not id_.startswith("-"):
                    func = element.lbo_commands[id_]
                    if int(bool(func.__command_is_global__)) >= only_globals:
                        result[id_] = func

    def on_command_clicked(self, event):
        self.input.value = event.target.command
        self._execute()
        stop_event(event)

    def on_blur(self, event):
        rtarget = event.relatedTarget
        if rtarget:
            if rtarget.parentElement == self.choice_div:
                stop_event(event)
                return

            if rtarget.tabIndex or rtarget.tabIndex == 0:
                self.current_target = None
        self._hide_minibuffer()
