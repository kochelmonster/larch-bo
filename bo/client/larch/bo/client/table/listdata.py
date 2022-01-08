
# __pragma__("skip")
console = document = window = None
def require(n): pass
# __pragma__ ("noskip")


class ListDataProvider:
    def ___init__(self, cv):
        super().__init__(cv)
        console.log("created list data provder", self.__name__)

    def get_visible_count(self):
        return len(self.context.value)

    def get_item(self, row):
        return self.context.value[row]
