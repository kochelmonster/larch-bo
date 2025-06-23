from ..i18n import pgettext
from ..command import label
from . import Grid


class OkCancel(Grid):
    i18n_context = "dialog"
    layout = """
[.ok]|(1em,0)|[.cancel]
"""

    @label(pgettext("dialog", "Ok"))
    def ok(self):
        return self.context.parent.control.ok()

    @label(pgettext("dialog", "Cancel"))
    def cancel(self):
        return self.context.parent.control.cancel()
