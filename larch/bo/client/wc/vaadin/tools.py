from larch.reactive import rule, Cell
from . import styles

# __pragma__("skip")
console = None
# __pragma__("noskip")


class MixinStyleObserver:
    def set_readonly(self, readonly):
        self.element.readonly = bool(readonly)

    def set_disabled(self, disabled):
        self.element.disabled = bool(disabled)

    def update_styles(self):
        for value in self.context.loop("disabled"):
            self.set_disabled(value)
        for value in self.context.loop("readonly"):
            self.set_readonly(value)

    @rule
    def _rule_styles(self):
        if self.element:
            self.update_styles()


class MixinVaadin:
    element = Cell()

    def unlink(self):
        super().unlink()
        self.element = None

    def get_tab_elements(self):
        return [self.element]
