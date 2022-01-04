"""an upload gui"""
from larch.reactive import Cell, rule
from ..i18n import label, create_number_formatter
from ..control import register
from ..grid import Grid
from ..textlayout import LayoutBuilder
from . import FileItem, FileUploader


# __pragma__("skip")
navigator = console = None
# __pragma__("noskip")


# just for msggettxt
def pgettext(context, n): return n


@register(FileUploader)
@register(FileUploader, "content")
class FileUploaderControl(Grid):
    layout = Cell("")

    @property
    def files(self):
        return self.context.value.files

    @property
    def file_count(self):
        return self.context.value.active_count

    @rule
    def _rule_update_layout(self):
        if self.file_count:
            yield
            builder = LayoutBuilder()
            rows = [builder.columns("[.files[{}]]".format(i)) for i in range(len(self.files))]
            rows.append(builder.columns("<1>"))
            self.layout = "\n".join(r.join() for r in rows)


@register(FileItem)
class FileItemControl(Grid):
    layout = """
[name_]{m}@text|[.sent_bytes_string]{rm}@text|(2em,0)|[.abort]{m}
pg:[sent_bytes]@progress
               |<1>                          |
"""

    @property
    def sent_bytes_string(self):
        return (to_human(self.context.value.sent_bytes, self.element)
                + "/" + to_human(self.context.value.size, self.element))

    def modify_controls(self):
        progress = self.celement("pg")
        progress.min = 0
        progress.max = self.context.value.size

    @label(pgettext("dialog", "Abort"))
    def abort(self):
        self.context.value.abort()


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
