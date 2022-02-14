"""
Javascript wrappers
"""
from collections import deque
from larch.reactive import rule, atomic, rcontext, Cell
from .control import OptionManager
from .browser import loading_modules, executer, PyPromise, fire_event
from .js.debounce import debounce
# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("vanilla-router")
document = loading_modules
JSON = __new__ = String = btoa = atob = console = window = None
def require(p): pass
def __pragma__(*args): pass
def __new__(*args): pass
# __pragma__("noskip")
# __pragma__('ecom')


Router = require("vanilla-router")


class ApplicationState(OptionManager):
    _hash_dirty = Cell(0)

    def __init__(self):
        super().__init__()
        self.synch_to_hash = debounce(self.synch_to_hash, 50)

    # super will not work in the next function because of jscall protcol!

    def set(self, control_id, item_id, value):
        key = f"{control_id}.{item_id}"
        if value is None:
            self.options.pop(key, None)
        else:
            OptionManager.set.call(self, key, value)
        self._hash_dirty += 1
        return self

    def get(self, control_id, item_id):
        return OptionManager.get.call(self, f"{control_id}.{item_id}")

    def loop(self, control_id, item_id):
        yield from OptionManager.loop.call(self, f"{control_id}.{item_id}")

    def observe(self, control_id, item_id):
        return OptionManager.observe.call(self, f"{control_id}.{item_id}")

    def synch_to_hash(self):
        # pack the optins in atree to save string space
        tree = self._options_to_tree()
        self._encode_to_hash(tree)

    def synch_from_hash(self):
        promise = PyPromise()

        __pragma__("ifdef", "socket")

        def set_state(result):
            self._tree_to_options(result)
            promise.resolve()

        def set_error(error):
            self._tree_to_options({})
            self._state_to_hash("")
            promise.resolve()

        packed = None
        __pragma__('js', '{}', '''
        try {
            packed = new Uint8Array(Buffer.from(window.location.hash.slice(1), "base64"));
        } catch(error) {
            console.warn("Cannot decode hash", error);
        }
        ''')
        if packed is not None:
            window.lbo.transmitter.decode(packed).then(set_state, set_error)
        else:
            set_state({})

        __pragma__("else")

        json = {}  # __:jsiter
        __pragma__('js', '{}', '''
        try {
            json = JSON.parse(atob(window.location.hash.slice(1)));
        } catch(error) {
            console.warn("Cannot decode hash", error, window.location.hash.slice(1));
        }
        ''')

        self._tree_to_options(json)
        promise.resolve()

        __pragma__("endif")
        return promise

    def _options_to_tree(self):
        tree = {}  # __:jsiter
        for k, v in self.options.items():
            path, name = k.rsplit(".", 1)
            level = tree
            for part in path.split("."):
                # __pragma__("jsiter")
                next_level = level[part]
                if not next_level:
                    next_level = level[part] = {}
                level = next_level
                # __pragma__("nojsiter")
            if type(v) == object:
                level[name+":"] = v
            else:
                level[name] = v
        return tree

    def _tree_to_options(self, tree):
        def iter_tree(level, prefix):
            # __pragma__("jsiter")
            for k in level:
                # __pragma__("nojsiter")
                v = level[k]
                if type(v) == object:
                    if k.endswith(":"):
                        yield prefix+k[:-1], v  # __:opov
                    else:
                        yield from iter_tree(v, prefix+k+".")
                else:
                    yield prefix+k, v

        with atomic():
            self._last_reactive_round = rcontext.rounds
            self.options = {}
            for k, v in iter_tree(tree, ""):
                self.options[k] = v
                if k in self.observed:
                    self.observed[k] = self._last_reactive_round

            self._observed_changed += 1

    def _state_to_hash(self, encoded):
        url = __new__(window.URL(window.location))
        url.hash = encoded
        window.history.replaceState(None, "", url)

    def _encode_to_hash(self, obj):
        __pragma__("ifdef", "socket")

        def pipe_to_hash(msgpacked):
            self._state_to_hash(btoa(String.fromCharCode.apply(None, msgpacked)))

        window.lbo.transmitter.encode(obj).then(pipe_to_hash)

        __pragma__("else")

        self._state_to_hash(btoa(JSON.stringify(obj)))

        __pragma__("endif")

    @rule
    def _rule_option_changed(self):
        if self._hash_dirty:
            # do not synch to hash from self._tree_top_options
            yield
            self.synch_to_hash()


__pragma__("ifdef", "socket")
"""?
from .server import transmitter
?"""
__pragma__("endif")

"""?
window.lbo.state = ApplicationState()
loading_modules.push(window.lbo.state.synch_from_hash().promise)
?"""


class Session:
    """
    A singlton that handles global management tasks for controls, like
      - keeping track of taborder
      - collecting all active commands and keystrokes

    Args:
        root (Control): The root of all Controls
    """

    def __init__(self, root):
        super().__init__()
        self.tasks = deque()
        self._active_dispatch_id = None
        self._wait_for_tabs = False
        self.router = __new__(Router({"mode": "history"}))  # __:jsiter
        self.root = root
        window.lbo.session = self

    def boot(self, container=None):
        """starts rendering"""
        if container is None:
            container = document.body

        document.addEventListener("new-tabs", self._update_tabindex)
        if self.transmitter:
            window.addEventListener("hashchange", self._synch_state)

        self.root.context.control = self.root.render(container)
        return self

    def add_route(self, path, callback):
        self.router.add(path, callback)

    def _save_state(self, event):
        state = event.detail
        window.lbo.state[state.id] = state
        del state.id
        self._commit_save_state()

    def _update_tabindex(self):
        if not self._wait_for_tabs:
            self._wait_for_tabs = True
            executer.add(self._build_tabindex)

    def _build_tabindex(self, root=None):
        root = root if root is not None else self.root
        tindex = 1000
        for c in root.get_tab_elements():
            c.tabIndex = tindex
            tindex += 1

        self._wait_for_tabs = False
        fire_event("tabindex-done")
