import larch.lib.adapter as adapter
# __pragma__("skip")
console = document = window = Promise = None
# __pragma__ ("noskip")


class TableDataProvider:
    def __init__(self, table):
        self.table = table

    @classmethod
    def set_table(cls, table):
        return cls(table)

    def render(self):
        pass


class ListDataProvider(TableDataProvider):
    def render(self):
        self.table.render_all(self.table.context.value)


adapter.register(list, TableDataProvider, "", ListDataProvider)


class DelayedDataProvider(TableDataProvider):
    placeholder = None
    data = None
    promise = None

    def __init__(self, table):
        self.table = table
        if table:
            self.resolve_data()

    def get_data(self):
        return self.__class__.data

    def set_data(self, data):
        self.__class__.data = data

    def load_data(self):
        raise NotImplementedError()

    def resolve_data(self):
        data = self.get_data()
        if data is None:
            def receive(data):
                console.log("***receive data")
                self.promise = None
                self.set_data(data)
                self.table.set_row_count(len(data))
                self.table.update_data()

            self.table.set_row_count(30)
            if not self.promise:
                self.promise = self.load_data()
            self.promise.then(receive)
        else:
            self.table.set_row_count(len(data))

    def request(self, start, end):
        data = self.get_data()
        if data:
            return data[start:end]
        return [self.placeholder for i in range(start, end)]
