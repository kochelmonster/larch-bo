"""PySide6 WebEngineWidgets Example"""
import logging
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView


logger = logging.getLogger('larch.bo.qt')


class Inspector(QMainWindow):
    def __init__(self, wid, page, instances):
        super().__init__()
        self.wid = wid
        self.instances = instances
        self.instances[wid] = self

        self.setWindowTitle('Inspector')
        self.view = QWebEngineView()
        self.view.page().setInspectedPage(page)

        self.setCentralWidget(self.view)
        self.view.page().titleChanged.connect(self.setWindowTitle)

    def closeEvent(self, event):
        self.instances.pop(self.wid, None)
        event.accept()
        if not self.instances:
            QApplication.instance().exit()
