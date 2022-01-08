from ...control import RenderingContext
from ...browser import loading_modules, BODY

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("@vaadin/dialog")
console = document = loading_modules
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import("@vaadin/dialog");
})());
''')


class DialogContentContext(RenderingContext):
    def render_to_container(self):
        pass


class Dialog:
    TAG = "vaadin-dialog"

    # __pragma__ ('kwargs')
    def __init__(self, value, parent=None, **kwargs):
        self.context = DialogContentContext(value, parent, dialog=self, **kwargs)
        self.result_callback = None
    # __pragma__ ('nokwargs')

    @property
    def element(self):
        return self.context.container

    @property
    def value(self):
        return self.context.value

    # __pragma__("kwargs")
    def modal(self, result_callback, style=None, klass=None, **kwargs):
        self.result_callback = result_callback
        dialog = document.createElement(self.TAG)
        dialog.renderer = self._render_into_dialog
        BODY.append(dialog)
        self.context.container = dialog
        for id_, value in kwargs.items():
            dialog[id_] = value
        dialog.opened = True
        if style is not None:
            dialog["$"].overlay["$"].overlay.style = style
        if klass is not None:
            dialog["$"].overlay["$"].overlay.className = klass
        dialog.addEventListener("opened-changed", self.on_open_changed)
    # __pragma__("nokwargs")

    def close(self):
        self.element.opened = False

    def render(self, parent):
        raise RuntimeError("Do not use render on Dialogs")

    def on_open_changed(self, event):
        if not self.element.opened:
            if self.result_callback:
                self.result_callback(self)
            self.element.remove()

    def _render_into_dialog(self, root, dialog):
        root.innerHTML = ""
        if self.context.control:
            self.context.control.render(root)
            self.context.update_tabindex()

    def unlink(self):
        super().unlink()
        if self.dialog is not None:
            self.dialog.remove()
        self.content_context.element = None

    def get_tab_elements(self):
        control = self.context.control
        return control.get_tab_elements() if control is not None else []
