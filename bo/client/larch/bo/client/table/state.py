from larch.reactive import rule
from ..js.debounce import debounce

# __pragma__("skip")
__new__ = DocumentFragment = console = document = window = None
# __pragma__ ("noskip")


class MixinState:
    waiting = True

    def __init__(self, cv):
        super().__init__(cv)
        self.save_state_to_hash = debounce(self.save_state_to_hash, 50)

    def save_state_to_hash(self):
        self.provider.save_state(self.get_state())

    @rule
    def _rule_state_changed(self):
        self.updated
        yield
        self.save_state_to_hash()
