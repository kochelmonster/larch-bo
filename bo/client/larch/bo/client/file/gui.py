"""an upload gui"""
from larch.reactive import Cell, rule
from ..control import register
from ..grid import Grid
from ..textlayout import LayoutBuilder
from ..browser import get_bubble_attribute
from . import FileItem, FileUploader


# __pragma__("skip")
navigator = None
# __pragma__("noskip")


@register(FileUploader)
class FileUploaderControl(Grid):
    layout = Cell()

    @property
    def files(self):
        return self.context.value.files

    @property
    def file_count(self):
        return self.context.value.active_count

    @rule
    def _rule_update_layout(self):
        self.file_count
        yield
        builder = LayoutBuilder()
        rows = [builder.columns("[.files[{}]]".format(i)) for i in range(len(self.files))]
        rows.append(builder.columns("<1>"))
        return "\n".join(r.join() for r in rows)


@register(FileItem)
class FileItemControl(Grid):
    layout = """
[name]|[.loaded_string]|[abort]
[loaded]@progress
"""

    @property
    def loaded_string(self):
        return to_human(self.value.loaded, self.lang)

    def render(self, parent):
        self.lang = get_bubble_attribute(parent, "lang", navigator.language)
        super().render(parent)


KILO = 1000
MEGA = 1000*KILO
GIGA = 1000*MEGA


def to_human(value, lang):
    if value > 10*GIGA:
        return int(value / 10*GIGA).toLocaleString(lang, {"style": "unit", "unit": "gigabyte"})
    elif value > 10*MEGA:
        return int(value / 10*MEGA).toLocaleString(lang, {"style": "unit", "unit": "megabyte"})
    elif value > 10*KILO:
        return int(value / 10*KILO).toLocaleString(lang, {"style": "unit", "unit": "kilobyte"})

    return value.toLocaleString(lang, {"style": "unit", "unit": "byte"})
