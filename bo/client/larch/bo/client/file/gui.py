"""an upload gui"""
from time import time
from larch.reactive import Cell, rule
from ..browser import get_icon, escape
from ..i18n import create_number_formatter, pgettext
from ..control import register
from ..grid import Grid
from ..command import label, icon
from ..textlayout import LayoutBuilder
from . import FileItem, FileUploader


# __pragma__("skip")
navigator = console = Option = None
def __pragma__(*args): pass
def __new__(p): pass
def pad2(n): pass
def require(n): pass
# __pragma__("noskip")


__pragma__("js", "{}", """
function pad2(number) {
  return (number < 10 ? '0' : '') + number;
}
""")

require("./larch.bo.file.scss")


@register(FileUploader)
@register(FileUploader, "content")
class FileUploaderControl(Grid):
    scrollable = True
    layout = Cell("")

    @property
    def files(self):
        return self.context.value.files

    def render(self, parent):
        self.update_layout()
        super().render(parent)
        self.element.classList.add("lbo-fileuploader")

    def update_layout(self):
        builder = LayoutBuilder()
        files = self.files
        rows = [builder.columns("[.files[{}]]".format(i))
                for i in range(len(files)) if not files[i].hidden]
        rows.append(builder.columns("<1>"))
        self.layout = "\n".join(r.join() for r in rows)


@register(FileItem)
class FileItemControl(Grid):
    layout = """
[.status]{m}@html|[.name_]{m}@html         |[.abort]{m}
                 |dt:[.details]@text       |
                 |pg:[sent_bytes]@progress |
                 |er:[error]@text          |
                 |       <1>               |
"""

    ACTIVE = "empty"
    ERROR = "error"
    COMPLETED = "check"
    BUTTON_THEME = "tertiary-inline"
    status = Cell("")
    element = Cell()

    @property
    def name_(self):
        return escape(self.context.value.name_)

    @property
    def details(self):
        value = self.context.value
        if value.sent_bytes == 0:
            return to_human(value.size, self.element)

        delta = time() - value.start
        seconds = int(value.size*(delta/value.sent_bytes) - delta)
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        togo = pad2(hours) + ":" + pad2(minutes) + ":" + pad2(seconds)
        return pgettext("file", "{size}:{part}(remaining time {time})").format(
            size=to_human(value.size, self.element),
            part=self.percent(value.sent_bytes/value.size), time=togo)

    def prepare_contexts(self):
        self.contexts["abort"].set("theme", self.BUTTON_THEME)

    def modify_controls(self):
        progress = self.celement("pg")
        progress.min = 0
        progress.max = self.context.value.size
        self.container("status").classList.add("part-status")
        self.container("name_").classList.add("part-name")
        self.container("dt").classList.add("part-detail")
        self.container("pg").classList.add("part-progress")
        self.container("er").classList.add("part-error")

    def render(self, parent):
        self.percent = create_number_formatter({"style": "percent"}, parent)
        super().render(parent)
        self.element.classList.add("lbo-fileitem")

    @icon("cross")
    @label("")
    def abort(self):
        fitem = self.context.value
        if fitem.status == "active":
            self.context.value.abort()
        else:
            fitem.hidden = True
            self.context.parent.control.update_layout()

    @rule
    def _rule_hide_elements(self):
        if self.element:
            status = self.context.value.status
            yield
            if status == "active":
                self.status = get_icon(self.ACTIVE)
                self.container("dt").style.display = ""
                self.container("pg").style.display = ""
                self.container("er").style.display = "none"
                self.container("abort").style.display = ""
                self.element.classList.remove("error")
            elif status == "completed":
                self.status = get_icon(self.COMPLETED)
                self.container("dt").style.display = "none"
                self.container("pg").style.display = "none"
                self.container("er").style.display = "none"
                self.element.classList.remove("error")
            elif status in ["aborted", "error"]:
                self.status = get_icon(self.ERROR)
                self.container("dt").style.display = "none"
                self.container("pg").style.display = "none"
                self.container("er").style.display = ""
                self.element.classList.add("error")


KILO = 1000
MEGA = 1000*KILO
GIGA = 1000*MEGA


def to_human(value, element):
    # __pragma__("jsiter")
    if value >= 10*GIGA:
        f = create_number_formatter({"style": "unit", "unit": "gigabyte"}, element)
        return f(value / (10*GIGA))
    elif value >= 10*MEGA:
        f = create_number_formatter({"style": "unit", "unit": "megabyte"}, element)
        return f(value / (10*MEGA))
    elif value >= 10*KILO:
        f = create_number_formatter({"style": "unit", "unit": "kilobyte"}, element)
        return f(value / (10*KILO))

    f = create_number_formatter({"style": "unit", "unit": "byte"}, element)
    # __pragma__("nojsiter")
    return f(value)
