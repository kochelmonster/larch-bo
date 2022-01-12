"""
Javascript wrappers
"""
from collections import deque
from .control import EventHandler
from .browser import loading_modules, executer
# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("vanilla-router")
document = loading_modules
console = window = None
def require(p): pass
def __pragma__(*args): pass
def create_router(): pass
# __pragma__("noskip")


__pragma__('ecom')


def set_transmitter(session):
    __pragma__("ifdef", "socket")
    """?
    from .server.transmitter import set_tmt
    set_tmt(session)
    ?"""
    __pragma__("endif")


__pragma__('js', '{}', '''
var Router = require("vanilla-router");
function create_router() {
    return new Router({mode: "history"})
}
''')


class Session(EventHandler):
    """
    A singlton that handles global management tasks, like
      - keeping track of taborder
      - collecting all active commands and keystrokes
      - interface to transmitter (server communication).
    Args:
        root (Control): The root of all Controls
    """

    def __init__(self, root):
        super().__init__()
        self.tasks = deque()
        self._active_dispatch_id = None
        self._wait_for_tabs = False
        self.router = create_router()
        self.root = root
        self.root.context.set("session", self)
        set_transmitter(self)
        window.session = self

    def boot(self, container=None):
        """starts rendering"""
        self.handle_event("new-tabs", self._update_tabindex)
        if container is None:
            container = document.body
        container.innerHTML = ""
        self.root.context.control = self.root.render(container)
        return self

    def add_route(self, path, callback):
        self.router.add(path, callback)

    def _update_tabindex(self):
        if not self._wait_for_tabs:
            self._wait_for_tabs = True
            executer.add(self._build_tabindex)

    def _build_tabindex(self, root=None):
        console.log("***build tabindex")
        root = root if root is not None else self.root
        tindex = 1000
        for c in root.get_tab_elements():
            c.tabIndex = tindex
            tindex += 1

        self._wait_for_tabs = False
        self.fire_event("tabindex-done")
