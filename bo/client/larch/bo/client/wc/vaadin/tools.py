from larch.reactive import rule, Cell


class MixinStyleObserver:
    def set_readonly(self, readonly):
        self.element.readonly = readonly

    def set_disabled(self, disabled):
        self.element.disabled = disabled

    def update_styles(self):
        self.set_disabled(self.context.observe("disabled") or False)
        self.set_readonly(self.context.observe("readonly") or False)

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
