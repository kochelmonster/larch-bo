"""
Javascript wrappers
"""
from collections import deque
from time import time
from .control import EventHandler
from .browser import loading_modules, BODY
# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("vanilla-router")
document = loading_modules
window = None
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


class SessionComunication:
    def get_translations(self, language):
        pass


class Session(EventHandler):
    MAX_TASK_TIME = 0.05

    def __init__(self, root_container=None):
        self.tasks = deque()
        self.translations = {}
        self._active_dispatch_id = None
        self._wait_for_tabs = False
        self.router = create_router()
        self.container = root_container or BODY
        set_transmitter(self)
        window.session = self

    def add_task(self, task, *args):
        self.tasks.append([task, args])
        if not self._active_dispatch_id:
            self._active_dispatch_id = window.requestAnimationFrame(self._dispatch_tasks)

    def set_root(self, root):
        self.root = root
        self.container.innerHTML = ""
        root.render(self.container)

    def add_route(self, path, creator):
        self.router.add(path, creator)

    def _dispatch_tasks(self):
        start = time()
        # __pragma__("tconv")
        while self.tasks:
            # __pragma__("notconv")
            func, args = self.tasks.popleft()
            func(*args)
            if time() - start > self.MAX_TASK_TIME:
                break

        if self.tasks:
            self._active_dispatch_id = window.requestAnimationFrame(self._dispatch_tasks)
        else:
            self._active_dispatch_id = None

    def update_tabindex(self):
        if not self._wait_for_tabs:
            self._wait_for_tabs = True
            self.add_task(self.build_tabindex)

    def build_tabindex(self, root=None):
        root = root if root is not None else self.root
        tindex = 1000
        for c in root.get_tab_elements():
            c.tabIndex = tindex
            tindex += 1

        self._wait_for_tabs = False
        self.fire_event("tabindex-done")

    def install_language(self, language):
        self.get_translations(language).then(self._set_translation)

    def _set_translation(self, translations):
        self.translations = translations["map"]
