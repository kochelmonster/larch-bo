import os
import logging
from time import time
from tempfile import NamedTemporaryFile
from gevent import spawn, sleep


logger = logging.getLogger("larch.bo.server.file")


class UploadFile:
    def __init__(self, file, destination):
        self.file_info = file
        self.destination = destination
        self.loaded = 0
        self.last_active = time()

    @property
    def id(self):
        return self.file_info["id"]

    def __repr__(self):
        path = self.file_info["path"]
        return f"<{self.__class__.__name__} {self.id} {path}>"

    def add(self, chunk):
        try:
            tmpfile = self.tmpfile
        except AttributeError:
            self.tmpfile = tmpfile = NamedTemporaryFile(delete=False)

        tmpfile.write(chunk)
        self.loaded += len(chunk)
        if self.loaded >= self.file_info["size"]:
            tmpfile.close()

        self.last_active = time()

    def unlink(self):
        try:
            tmpfile = self.tmpfile
        except AttributeError:
            return
        del self.tmpfile
        tmpfile.close()
        try:
            os.unlink(tmpfile.name)
        except (IOError, AttributeError):
            logger.exception("error removing tempfile %r", self)


class FileUploader:
    """Mixin to handle fileuploads"""
    PURGE_TIME = 20 * 60

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_uploads = {}
        self._file_upload_monitor_greenlet = None

    def file_upload_start(self, destination, files, accept):
        logger.debug("file_upload_start %r\n%r", destination, files)
        ids = self.file_accept_uploads(destination, files, accept)
        for f in files:
            if f["id"] in ids:
                self.file_uploads[f["id"]] = UploadFile(f, destination)
        if ids and self._file_upload_monitor is None:
            self._file_upload_monitor_greenlet = spawn(self._file_upload_monitor)

        return ids

    def file_accept_uploads(self, destination, files, accept):
        return {f["id"]: True for f in files}

    def file_upload_chunk(self, id_, chunk):
        logger.debug("file_upload_chunk %r %r", id_, len(chunk))
        state = "continue"
        try:
            file_ = self.file_uploads[id_]
            if file_.add(chunk):
                state = "finished"
                self.file_done_upload(file_)
        except Exception:
            logger.exception("Error uploading chunk %r", id_)
            state = "error"

        return {"id": id_, "state": state}

    def file_upload_abort(self, id_):
        logger.debug("file_upload_abort %r", id_)
        try:
            file_ = self.file_uploads.pop(id_)
            file_.unlink()
            logger.debug("aborted upload %r", id_)
        except KeyError:
            pass

    def _file_upload_monitor(self):
        try:
            delta = self.PURGE_TIME / 4
            while self.file_uploads:
                sleep(delta)
                now = time()
                for fitem in list(self.file_uploads.values()):
                    if now - fitem.last_active > self.PURGE_TIME:
                        logger.debug("upload file inactive %r", fitem)
                        fitem.unlink()
                        self.file_uploads.pop(fitem.id, None)
        finally:
            self._file_upload_monitor_greenlet = None
