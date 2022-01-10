"""file transfer functions"""
from time import time
from larch.reactive import Reactive, Cell
from ..browser import executer, create_promise, loading_modules
from ..i18n import pgettext

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
    status = Cell("active")
    error = Cell("")
    hidden = False

    def __init__(self, ofile, uploader):
        self.start = 0
        self.ofile = ofile
        self.uploader = uploader
        self.id = uuidv4()
        self.request = None
        self.uploaded_bytes = 0

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.ofile.name}, {self.size} {self.status}>"

    @property
    def name_(self):
        return self.ofile["name"]

    @property
    def size(self):
        return self.ofile.size

    def pipe(self, file_reader):
        if self.status == "active" and self.uploaded_bytes <= self.sent_bytes:
            blob = self.ofile.slice(
                self.uploaded_bytes, min(self.uploaded_bytes+CHUNK_SIZE, self.size))
            file_reader.readAsArrayBuffer(blob)
            return True
        return False

    def upload(self, event):
        if self.status == "active":
            if self.uploaded_bytes == 0:
                self.start = time()
            self.uploaded_bytes += event.target.result.byteLength
            if self.request is None:
                self.request = window.transmitter.put_start(
                    "file_upload", event.target.result, id_=self.id)
                self.request.then(self._check_upload_state, self._error_upload).receive(
                    self._commited_upload)
            else:
                self.request.put(event.target.result)

    def abort(self, status="aborted", msg=None):
        console.log("**abort", repr(self))
        if self.status == "active":
            if msg is None:
                self.error = str(pgettext("file", "Aborted"))
            else:
                self.error = str(msg)
            self.status = status
            if self.request is not None:
                self.request.abort()
                self.request = None
            self.uploader.update_active_count()

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
        if self.sent_bytes >= self.size:
            self.status = "completed"
            self.uploader.update_active_count()

    def _check_upload_state(self, state):
        pass

    def _error_upload(self, state):
        console.warn("error uploading", state)
        self.abort("error", pgettext("file", "An error occured"))


class FileUploader(Reactive):
    active_count = Cell(1)
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
        document.body.appendChild(controller)
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

    def _upload_chunk(self, event):
        active = self.files[self.active_index]
        if active is not None:
            active.upload(event, self)
        executer.add(self.upload_next)

    def _error(self, event):
        active = self.files[self.active_index]
        if active is not None:
            console.warn("error reading file", repr(active), event)
            active.abort("error", pgettext("file", "An error occured"))
        self.upload_next()

    def update_active_count(self):
        self.active_count = len([f for f in self.files if f.status == "active"])

    def start_upload(self, files):
        self.files = [FileItem(f, self) for f in files]
        self.file_reader = __new__(FileReader())
        self.file_reader.onload = self._upload_chunk
        self.file_reader.onerror = self._error
        window.session.extern.file_upload_start(
            self.destination, [f.pack() for f in self.files], self.accept).then(
                self._accept, self.abort)

    def upload_next(self):
        active_count = 0
        for i in range(len(self.files)):
            self.active_index += 1
            if self.active_index >= len(self.files):
                self.active_index = 0

            active = self.files[self.active_index]
            if active.status == "active":
                active_count += 1

            if active.pipe(self.file_reader):
                return

        if active_count:
            window.setTimeout(self.upload_next, 100)

    def _accept(self, ids):
        self.files = [f for f in self.files if f.id in ids]
        self.upload_next()
        if self._start_callback is not None:
            self._start_callback(self)
