"""file transfer functions"""
from larch.reactive import Reactive, Cell
from ..browser import BODY, executer, create_promise, loading_modules

# __pragma__("skip")

from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.add("uuid")
document = window = loading_modules
def __pragma__(*args): pass
# __pragma__("noskip")


uuidv4 = None
__pragma__('js', '{}', '''
loading_modules.push((async () => {
    uuidv4 = await import('uuid');
})());
''')


CHUNK_SIZE = 64*1024


class FileItem(Reactive):
    send = Cell(0)

    def __init__(self, ofile, uploader):
        self.ofile = ofile
        self.uploader = uploader
        self.completed = self.aborted = False
        self.id = uuidv4()

    @property
    def size(self):
        return self.ofile.size

    def pipe(self, file_reader):
        if not self.completed:
            blob = self.ofile.slice(self.send, min(self.send+CHUNK_SIZE, self.size))
            file_reader.readAsArrayBuffer(blob)
            return True
        return False

    def upload(self, event):
        self.send += event.target.result.byteLength
        if not self.completed:
            window.session.extern.file_upload_chunk(self.id, event.target.result).then(
                self._check_upload_state)
            self.completed = self.send >= self.size

        return self.completed

    def abort(self):
        self.aborted = True
        window.session.extern.file_upload_abort(self.uploader.destination, self.id)
        self.uploader.remove(self.id)

    def pack(self):
        f = self.ofile
        return {
            "id": self.id,
            "modified": f.lastModified,
            "name": f["name"],
            "size": f.size,
            "mime": f.type,
            "path": f.path or f.fullPath or f.filepath or f.webkitRelativePath or f.name}

    def _check_upload_state(self, state):
        if state.get("state", "error") == "error":
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

    def remove(self, id_):
        self.files = [f for f in self.files if f.id != id_]
        self.active_count = len(self.files)
        self.active_index = min(self.active_index, self.active_count-1)

    def _upload_chunk(self, event):
        active = self.files[self.active_index]
        if active is not None and active.upload(event, self):
            self.remove(active.id)
        executer.add(self.upload_next)

    def _error(self, event):
        active = self.files[self.active_index]
        if active is not None:
            active.abort()
        self.upload_next()

    def start_upload(self, files):
        self.files = [FileItem(f) for f in files]
        __pragma__('js', '{}', '''
        self.file_reader = new FileReader();
        ''')
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

            if self.files[self.active_index].pipe(self.file_reader):
                return

    def _accept(self, ids):
        self.files = [f for f in self.files if f.id in ids]
        self.active_count = len(self.files)
        self.upload_next()
        if self._start_callback is not None:
            self._start_callback(self)
