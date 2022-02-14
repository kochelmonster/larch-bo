from larch.reactive import rule, Cell
from ...control import Control, register as cregister
from ...browser import loading_modules
from .tools import MixinVaadin, MixinStyleObserver

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.update(["@vaadin/checkbox"])
console = document = loading_modules
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import('@vaadin/checkbox');
})());
''')


class CheckboxControl(MixinVaadin, MixinStyleObserver, Control):
    TAG = "vaadin-checkbox"
    element = Cell()

    def render(self, parent):
        self.element = document.createElement(self.TAG)
        parent.appendChild(self.element)
        self.element.addEventListener("change", self.on_change)
        label = self.context.get("label-element")
        if label:
            label.setAttribute("for", self.element.inputElement.id)
        self.update_styles()

    def on_change(self, event):
        self.context.value = self.element.checked

    def set_readonly(self, readonly):
        self.element.disabled = readonly

    @rule
    def _rule_value_changed(self):
        if self.element:
            self.element.checked = self.context.value


def register(style=""):
    cregister(type(True), style)(CheckboxControl)
