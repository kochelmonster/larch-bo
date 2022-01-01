from ..i18n import label
from . import Grid


# just for msggettxt
def pgettext(context, n): return n


class OkCancel(Grid):
    i18n_context = "dialog"
    layout = """
[.ok]|[.cancel]
"""

    @label(pgettext("dialog", "Ok"))
    def ok(self):
        return self.context.parent.control.ok()

    @label(pgettext("dialog", "Cancel"))
    def cancel(self):
        return self.context.parent.control.cancel()
