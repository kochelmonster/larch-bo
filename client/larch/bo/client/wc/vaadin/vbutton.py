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
        self.set_default_label()
        self.set_default_icons()
        self.set_default_tooltip()
        self.update_styles()

    def on_click(self, event):
        self.context.value()

    def set_default_label(self):
        label = get_func_prop(self.context.value, "__label__")
        if label is None:
            label = self.context.get("name")
        self.element.innerText = str(label)

    def set_default_icons(self):
        el = self.element

        icon = get_func_prop(self.context.value, "__icon__")
        if icon:
            icon = get_icon(icon)
            add_slot(el, "prefix" if el.innerText else None, icon)

        icon = get_func_prop(self.context.value, "__ricon__")
        if icon:
            icon = get_icon(icon)
            add_slot(el, "suffix", icon)

    def set_default_tooltip(self):
        tooltip = get_func_prop(self.context.value, "__tooltip__")
        if tooltip:
            self.element.dataset.tooltip = str(tooltip)

    def update_styles(self):
        super().update_styles()
        element = self.element
        for label in self.context.loop("label"):
            element.innerText = str(label)

        for icon in self.context.loop("prefix"):
            add_slot(element, "prefix" if element.innerText else None, icon)

        for icon in self.context.loop("suffix"):
            add_slot(element, "suffix", icon)

        for tooltip in self.context.loop("tooltip"):
            if tooltip:
                self.element.dataset.tooltip = str(tooltip)
            else:
                __pragma__("js", "{}", "delete self.element.dataset.tooltip;")

        for theme in self.context.loop("theme"):
            self.element.setAttribute("theme", theme)


def register(style=""):
    cregister(type(cregister), style)(ButtonControl)
