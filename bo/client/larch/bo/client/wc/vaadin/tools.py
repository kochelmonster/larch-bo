from larch.reactive import rule


class MixinDisabled:
    def set_readonly(self, readonly):
        self.element.readonly = readonly

    def set_disabled(self, disabled):
        self.element.disabled = disabled

    @rule
    def _rule_styles(self):
        if self.element:
            self.set_disabled(self.context.observe("disabled") or False)
            self.set_readonly(self.context.observe("readonly") or False)
