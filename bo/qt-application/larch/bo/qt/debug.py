"""PySide6 WebEngineWidgets Example"""
import logging
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Signal, QFileSystemWatcher


logger = logging.getLogger('larch.bo.qt')


class Inspector(QMainWindow):
    closed = Signal()

    def __init__(self, page):
        super().__init__()

        self.setWindowTitle('Inspector')
        self.view = QWebEngineView()
        self.view.page().setInspectedPage(page)

        self.setCentralWidget(self.view)
        self.view.page().titleChanged.connect(self.setWindowTitle)

    def closeEvent(self, event):
        super().closeEvent(event)
        self.closed.emit()


def install_watcher(config, browser_windows):
    def reload_all(path):
        logger.info("reload code")
        for w in list(browser_windows):
            w.reload()

    watcher = QFileSystemWatcher([str(config.get("resource_path"))], QApplication.instance())
    watcher.directoryChanged.connect(reload_all)
    logger.info("started watcher\n%r", watcher.directories())
