from larch.reactive import rule
from larch.bo.client.control import Control, RenderingContext
from larch.bo.client.browser import loading_modules, BODY

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("@vaadin/dialog")
document = loading_modules
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import("@vaadin/dialog");
})());
''')


class DialogContentContext(RenderingContext):
    def render_to_element(self):
        pass


class Dialog(Control):
    TAG = "vaadin-dialog"

    def __init__(self, cv=None):
        super().__init__(cv)
        self.content_context = DialogContentContext(None, self.context)
        self.result_callback = None

    @property
    def element(self):
        return self.content_context.element

    @property
    def value(self):
        return self.context.value

    # __pragma__("kwargs")
    def modal(self, result_callback, **kwargs):
        self.context.control = self
        self.result_callback = result_callback
        dialog = document.createElement(self.TAG)
        dialog.renderer = self._render_into_dialog
        BODY.append(dialog)
        self.content_context.element = dialog
        for id_, value in kwargs.items():
            dialog[id_] = value
        dialog.opened = True
        dialog.addEventListener("opened-changed", self.on_open_changed)
    # __pragma__("nokwargs")

    def close(self):
        self.element.opened = False

    def render(self, parent):
        raise RuntimeError("Do not use render on Dialogs")

    def on_open_changed(self, event):
        print("on_open_changed", event, self.element.opened)
        if not self.element.opened:
            if self.result_callback:
                self.result_callback(self)
            self.element.remove()

    def _render_into_dialog(self, root, dialog):
        root.innerHTML = ""
        if self.content_context.control:
            self.content_context.control.render(root)
            self.content_context.update_tabindex()

    def unlink(self):
        super().unlink()
        if self.dialog is not None:
            self.dialog.remove()
        self.content_context.element = None

    def get_tab_elements(self):
        control = self.content_control.control
        return control.get_tab_elements() if control is not None else []

    @rule
    def _rule_synch_values(self):
        self.content_context.value = self.context.value
