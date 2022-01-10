from ...control import Control, register as cregister
from ...browser import loading_modules, get_icon, add_slot
from ...command import get_func_prop
from .tools import MixinVaadin, MixinStyleObserver

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("@vaadin/button")
console = document = loading_modules
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import("@vaadin/button");
})());
''')


class ButtonControl(MixinVaadin, MixinStyleObserver, Control):
    TAG = "vaadin-button"

    def render(self, parent):
        self.element = document.createElement(self.TAG)
        parent.appendChild(self.element)
        self.element.addEventListener("click", self.on_click)

    def on_click(self, event):
        self.context.value()

    def update_styles(self):
        super().update_styles()
        element = self.element
        label = self.context.observe("label")
        if not label and not isinstance(label, str):
            label = get_func_prop(self.context.value, "__label__")

            if not label and not isinstance(label, str):
                label = self.context.observe("name")

        element.innerText = str(label)
        icon = self.get_icon("prefix", "__icon__")
        if icon:
            add_slot(element, "prefix" if label else None, icon)

        icon = self.get_icon("suffic", "__ricon__")
        if icon:
            add_slot(element, "suffix", icon)

        return self.update_tooltip().update_theme()

    def get_icon(self, slot, alt):
        icon = self.context.observe(slot)
        if not icon:
            icon = get_func_prop(self.context.value, alt)
        if icon:
            icon = get_icon(icon)
        return icon

    def update_tooltip(self):
        tooltip = self.context.observe("tooltip")
        if not tooltip:
            tooltip = get_func_prop(self.context.value, "__tooltip__")
        if tooltip:
            self.element.dataset.tooltip = str(tooltip)
        else:
            __pragma__("js", "{}", "delete self.element.dataset.tooltip;")
        return self

    def update_theme(self):
        theme = self.context.observe("theme") or ""
        self.element.setAttribute("theme", theme)


def register(style=""):
    cregister(type(cregister), style)(ButtonControl)
