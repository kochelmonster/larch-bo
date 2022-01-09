from larch.reactive import rule, Cell
from ...control import Control, register as cregister
from ...browser import loading_modules, LiveTracker
from .tools import MixinDisabled

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.update([
    "@vaadin/number-field", "@vaadin/integer-field", "@vaadin/text-field"])
console = document = loading_modules
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import('@vaadin/text-field');
    await import("@vaadin/number-field");
    await import("@vaadin/integer-field");
})());
''')


class TextControl(MixinDisabled, Control):
    TAG = "vaadin-text-field"
    element = Cell()

    def render(self, parent):
        self.element = document.createElement(self.TAG)
        parent.appendChild(self.element)
        self.element.addEventListener("change", self.on_change)
        label = self.context.get("label-element")
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


class IntControl(TextControl):
    TAG = "vaadin-number-field"


class FloatControl(TextControl):
    TAG = "vaadin-number-field"


def register(style=""):
    cregister(type(""), style)(TextControl)
    cregister(type(2), style)(IntControl)
    cregister(type(2.1), style)(FloatControl)
