"""file transfer functions"""
from larch.reactive import Reactive, Cell
from ..browser import BODY, executer, create_promise, loading_modules

# __pragma__("skip")

from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("uuid")
FileReader = console = document = window = loading_modules
def __pragma__(*args): pass
def __new__(a): pass
# __pragma__("noskip")


uuidv4 = None
__pragma__('js', '{}', '''
loading_modules.push((async () => {
    uuidv4 = await import('uuid');
})());
''')


CHUNK_SIZE = 32*1024


class FileItem(Reactive):
    sent_bytes = Cell(0)

    def __init__(self, ofile, uploader):
        self.ofile = ofile
        self.uploader = uploader
        self.aborted = False
        self.id = uuidv4()
        self.request = None
        self.uploaded_bytes = 0

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.ofile.name}, {self.size}>"

    @property
    def name_(self):
        return self.ofile["name"]

    @property
    def size(self):
        return self.ofile.size

    @property
    def completed(self):
        return self.sent_bytes >= self.size

    def pipe(self, file_reader):
        if self.uploaded_bytes <= self.sent_bytes:
            blob = self.ofile.slice(self.sent_bytes, min(self.sent_bytes+CHUNK_SIZE, self.size))
            file_reader.readAsArrayBuffer(blob)
            return True
        return False

    def upload(self, event):
        if not self.completed:
            self.uploaded_bytes += event.target.result.byteLength
            if self.request is None:
                self.request = window.transmitter.put_start(
                    "file_upload", event.target.result, id_=self.id)
                self.request.then(self._check_upload_state, self._error_upload).receive(
                    self._commited_upload)
            else:
                self.request.put(event.target.result)

    def abort(self):
        self.aborted = True
        if self.request is not None:
            self.request.abort()
            self.request = None
        self.uploader.remove(self.id)

    def pack(self):
        f = self.ofile
        # __pragma__("jsiter")
        return {
            "id": self.id,
            "modified": f.lastModified,
            "name": f["name"],
            "size": f.size,
            "mime": f.type,
            "path": f.path or f.fullPath or f.filepath or f.webkitRelativePath or f.name}
        # __pragma__("nojsiter")

    def _commited_upload(self, bytes_done):
        self.sent_bytes += bytes_done

    def _check_upload_state(self, state):
        pass

    def _error_upload(self, state):
        console.warn("error uploading", state)
        self.abort()


class FileUploader(Reactive):
    active_count = Cell()
    _start_callback = None

    def __init__(self, accept="", mode="", destination="default"):
        self.accept = accept
        self.mode = mode
        self.destination = destination
        self.file_reader = None
        self.active_index = 1

    def open_dialog(self):
        controller = document.createElement("input")
        __pragma__('js', '{}', '''
        controller.type = "file"
        ''')

        if "multi" in self.mode:
            controller.multiple = True
        if "directory" in self.mode:
            controller.webkitdirectory = True
        if self.accept:
            controller.accept = self.accept

        controller.style.position = "absolute"
        BODY.appendChild(controller)
        controller.click()
        controller.remove()
        controller.onchange = lambda event: self.start_upload(event.target.files)
        return create_promise(self._set_start_callback)

    def _set_start_callback(self, resolve):
        self._start_callback = resolve

    def abort(self):
        if self.file_reader is not None:
            self.file_reader.abort()
            self.file_reader = None
        for f in list(self.files):
            f.abort()
        self.active_count = 0

    def remove(self, id_):
        self.files = [f for f in self.files if f.id != id_]
        self.active_count = len(self.files)
        self.active_index = min(self.active_index, self.active_count-1)

    def _upload_chunk(self, event):
        active = self.files[self.active_index]
        if active is not None:
            active.upload(event, self)
        executer.add(self.upload_next)

    def _error(self, event):
        active = self.files[self.active_index]
        if active is not None:
            active.abort()
        self.upload_next()

    def start_upload(self, files):
        self.files = [FileItem(f, self) for f in files]
        self.file_reader = __new__(FileReader())
        self.file_reader.onload = self._upload_chunk
        self.file_reader.onerror = self._error

        window.session.extern.file_upload_start(
            self.destination, [f.pack() for f in self.files], self.accept).then(
                self._accept, self.abort)

    def upload_next(self):
        for i in range(len(self.files)):
            self.active_index += 1
            if self.active_index >= len(self.files):
                self.active_index = 0

            active = self.files[self.active_index]
            if active.completed:
                self.remove(active.id)
            else:
                if active.pipe(self.file_reader):
                    return

        if len(self.files):
            window.setTimeout(self.upload_next, 100)

    def _accept(self, ids):
        self.files = [f for f in self.files if f.id in ids]
        self.active_count = len(self.files)
        self.upload_next()
        if self._start_callback is not None:
            self._start_callback(self)
