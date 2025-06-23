from larch.reactive import rule, Cell
from ...control import Control, register as cregister
from ...browser import loading_modules, LiveTracker

# __pragma__("skip")
from larch.bo.packer import parcel
document = loading_modules
parcel.NEEDED_PACKAGES.add("@polymer/paper-input")
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import('@polymer/paper-input/paper-input.js');
})());
''')


class TextControl(Control):
    TAG = "paper-input"
    element = Cell()

    def render(self, parent):
        self.element = document.createElement("paper-input")
        parent.appendChild(self.element)
        self.element.addEventListener("change", self.on_change)
        label = self.context.get("label")
        if label:
            label.setAttribute("for", self.element.inputElement.id)

    def unlink(self):
        super().unlink()
        self.element = None

    def get_tab_elements(self):
        return [self.element]

    def on_change(self, event):
        self.context.value = self.element.value

    def live(self):
        self._old_value = self.element.value
        self.tracker = LiveTracker(self._watch_for_change)
        return self

    def _watch_for_change(self):
        if self._old_value != self.element.value:
            self.context.value = self._old_value = self.element.value

    @rule
    def _rule_value_changed(self):
        if self.element:
            self.element.setAttribute("value", self.context.value)


def register(style=""):
    cregister(type(""), style)(TextControl)
