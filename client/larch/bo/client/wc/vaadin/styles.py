from ...browser import loading_modules, register_icon
from . import icon

# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("@vaadin/vaadin-lumo-styles")
loading_modules
icon
def require(p): pass
def __pragma__(*args): pass
# __pragma__("noskip")


__pragma__('js', '{}', '''
loading_modules.push((async () => {
    await import("@vaadin/vaadin-lumo-styles");
})());
''')


require("./larch.bo.vaadin.scss")


def ricon(lbo_id, vaadin_id):
    register_icon(lbo_id, f'<vaadin-icon icon="{vaadin_id}"></vaadin-icon>')


ricon("error", "lumo:error")
ricon("check", "lumo:checkmark")
ricon("cross", "lumo:cross")
ricon("empty", "")
