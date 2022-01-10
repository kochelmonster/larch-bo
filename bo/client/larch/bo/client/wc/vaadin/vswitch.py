from larch.reactive import rule
from ...control import Control, register as cregister
from ...browser import loading_modules
from .tools import MixinVaadin, MixinStyleObserver

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.update(["jelly-switch"])
console = document = loading_modules
def __pragma__(*args): pass
def require(p): pass

# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import('jelly-switch');
})());
''')


class SwitchControl(MixinVaadin, MixinStyleObserver, Control):
    TAG = "jelly-switch"

    def render(self, parent):
        self.element = document.createElement(self.TAG)
        self.element.checked = self.context.value
        parent.appendChild(self.element)
        self.element.addEventListener("toggle", self.on_change)

    def on_change(self, event):
        self.context.value = self.element.checked

    def set_readonly(self, readonly):
        self.element.disabled = readonly

    @rule
    def _rule_value_changed(self):
        if self.element:
            self.element.checked = bool(self.context.value)


def register(style=""):
    if style:
        style = "." + style
    cregister(type(True), "switch"+style)(SwitchControl)
