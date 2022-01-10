from larch.reactive import rule
from ...control import Control, register as cregister
from ...browser import loading_modules
from .tools import MixinVaadin

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("@vaadin/progress-bar")
console = document = loading_modules
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import("@vaadin/progress-bar");
})());
''')


class ProgressControl(MixinVaadin, Control):
    TAG = "vaadin-progress-bar"

    def render(self, parent):
        self.element = document.createElement(self.TAG)
        parent.appendChild(self.element)

    def get_tab_elements(self):
        return []

    @rule
    def _rule_update_value(self):
        if self.element:
            self.element.value = self.context.value


def register(style=""):
    if style:
        style = "." + style
    cregister(type(1), "progress" + style)(ProgressControl)
    cregister(type(1.1), "progress" + style)(ProgressControl)
