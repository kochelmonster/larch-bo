from larch.reactive import rule
from ...control import Control, register as cregister
from ...browser import loading_modules, LiveTracker
from .tools import MixinVaadin, MixinStyleObserver

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.update([
    "@vaadin/number-field", "@vaadin/integer-field", "@vaadin/text-field",
    "@vaadin/password-field", "@vaadin/email-field", "@vaadin/text-area"])
console = document = loading_modules
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import('@vaadin/text-field');
    await import("@vaadin/number-field");
    await import("@vaadin/integer-field");
    await import("@vaadin/text-area");
    await import("@vaadin/password-field");
    await import("@vaadin/email-field");
})());
''')


class TextControl(MixinVaadin, MixinStyleObserver, Control):
    TAG = "vaadin-text-field"

    def render(self, parent):
        element = document.createElement(self.TAG)
        parent.appendChild(element)

        # <input slot="input" tabindex="1001">

        self.element = element
        label = self.context.get("label-element")
        if label:
            label.setAttribute("for", self.element.inputElement.id)

        element.addEventListener("change", self.on_change)

    def get_tab_elements(self):
        return [self.element.inputElement]

    def on_change(self, event):
        self.context.value = self.element.value

    def live(self):
        self._old_value = self.element.value
        self.tracker = LiveTracker(self._watch_for_change)
        return self

    def _watch_for_change(self):
        if self._old_value != self.element.value:
            self.context.value = self._old_value = self.element.value

    def update_styles(self):
        super().update_styles()
        self.element.autocomplete = self.context.observe("autocomplete") or "nope"

    @rule
    def _rule_value_changed(self):
        if self.element:
            self.element.setAttribute("value", self.context.value)


class EmailControl(TextControl):
    TAG = "vaadin-email-field"


class PasswordControl(TextControl):
    TAG = "vaadin-password-field"


class IntControl(TextControl):
    TAG = "vaadin-number-field"


class FloatControl(TextControl):
    TAG = "vaadin-number-field"


class TextAreaControl(TextControl):
    TAG = "vaadin-text-area"


def register(style=""):
    cregister(type(""), style)(TextControl)
    cregister(type(2), style)(IntControl)
    cregister(type(2.1), style)(FloatControl)
    if style:
        style = "."+style
    cregister(type(""), "multi"+style)(TextAreaControl)
    cregister(type(""), "password"+style)(PasswordControl)
    cregister(type(""), "email"+style)(EmailControl)
