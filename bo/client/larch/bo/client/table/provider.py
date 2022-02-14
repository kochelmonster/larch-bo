import larch.lib.adapter as adapter
from ..js.debounce import debounce
# __pragma__("skip")
console = document = window = Promise = None
# __pragma__ ("noskip")


class TableDataProvider:
    # __pragma__("kwargs")
    def __init__(self, table=None):
        # __pragma__("nokwargs")
        self.table = table

    @classmethod
    def set_table(cls, table):
        table.provider = cls(table)

    def request(self, start, end):
        raise NotImplementedError()

    def save_state(self, state):
        window.lbo.state.set(self.table.context.get("id"), "table", state)

    def load_state(self):
        return window.lbo.state.get(self.table.context.get("id"), "table")


class ListDataProvider(TableDataProvider):
    # __pragma__("kwargs")
    def __init__(self, table):
        # __pragma__("nokwargs")
        self.table = table
        self.table.set_state(self.load_state())
        self.table.set_row_count(len(self.table.context.value))

    def request(self, start, end):
        return self.table.context.value[start:end]


adapter.register(list, TableDataProvider, "", ListDataProvider)


class DelayedDataProvider(TableDataProvider):
    PLACEHOLDER_COUNT = 30
    PLACEHOLDER = None
    data = None
    promise = None

    @classmethod
    def set_table(cls, table):
        table.provider = cls(table)
        table.provider.resolve_data()

    def get_data(self):
        return self.__class__.data

    def set_data(self, data):
        self.__class__.data = data

    def load_data(self):
        raise NotImplementedError()

    def resolve_data(self):
        state = self.load_state()

        data = self.get_data()
        if data is None:
            def receive(data):
                self.promise = None
                self.set_data(data)
                self.table.set_state(state)
                self.table.set_row_count(len(data))
                self.table.update_data()

            self.table.set_row_count(self.PLACEHOLDER_COUNT)
            if not self.promise:
                self.promise = self.load_data()
            self.promise.then(receive)
        else:
            self.table.set_state(state)
            self.table.set_row_count(len(data))

    def request(self, start, end):
        data = self.get_data()
        if data:
            return data[start:end]
        return [self.PLACEHOLDER for i in range(start, end)]


class DelayedChunkProvider(TableDataProvider):
    """
    This proider loads only the necessary chunks from server
    the server has to deilver chunked data:
    {
        count: int            # the complete data size
        chunk_size: int       # the size of chunks (must always be the same)
        start: int            # the start row of the delivered chunk
        data: [records]       # array of records
    }
    """

    PLACEHOLDER_COUNT = 30
    PLACEHOLDER = None
    """must be set by child classes, a record for placeholder data,
    must contain a "__placeholder__" field"""

    def __init__(self, table=None):
        self.table = table
        self.request_chunk = debounce(self.request_chunk, 50)

    @classmethod
    def set_table(cls, table):
        table.provider = cls(table)
        container = table.provider.make_chunk_container()
        state = table.provider.load_state()

        count = container.count or state.count or table.provider.PLACEHOLDER_COUNT
        table.set_state(state)
        table.set_row_count(count)

    def save_state(self, state):
        state.count = self.table.row_count
        super().save_state(state)

    def make_chunk_container(self):
        container = self.__class__.data_chunks
        if not container:
            # __pragma__("jsiter")
            container = self.__class__.data_chunks = {
                "count": None,
                "chunk_size": 1,
                "promises": {}
            }
            # __pragma__("nojsiter")
        return container

    def load_chunk(self, row):
        raise NotImplementedError()

    def request_chunk(self, row):
        container = self.make_chunk_container()
        if not container.promises[row]:
            container.promises[row] = self.load_chunk(row).then(self.receive)

    def receive(self, chunk):
        container = self.make_chunk_container()
        del container.promises[chunk.start]
        container[chunk.start] = chunk.data
        container.chunk_size = chunk.chunk_size
        container.count = chunk.count
        if chunk.count != self.table.row_count:
            self.table.set_row_count(chunk.count)
        if (self.table.row_start < chunk.start + chunk.chunk_size
                and chunk.start < self.table.row_end):
            self.table.update_data()

    def request(self, start, end):
        container = self.make_chunk_container()
        result = []
        chunk_size = container.chunk_size

        start_index = start % chunk_size
        chunk_start = int(start/chunk_size)*chunk_size
        for i in range(chunk_start, end, chunk_size):
            chunk = container[i]
            if chunk:
                result.extend(chunk[start_index:])
                start_index = 0
            else:
                self.request_chunk(i)
                return [self.PLACEHOLDER for i in range(start, end)]
        return result[:end-start]
