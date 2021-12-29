"""Standalone Browser for larch browser object"""
import sys
import logging
from pathlib import Path
from PySide6.QtCore import QUrl, Qt, QEvent, QFile, QObject, Slot, QJsonValue, QPoint
from PySide6.QtGui import QColor, QAction
from PySide6.QtWidgets import QApplication, QMainWindow, QMenu
from PySide6.QtWebEngineCore import (
    QWebEnginePage, QWebEngineUrlRequestInterceptor, QWebEngineProfile)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel


logger = logging.getLogger('larch.bo.qt')

"""
TODO:
 - Start python
   - client imports for python skippen
   - transmitter mit config einstellen

 - laden von resourcen durch redirect
 - kein transmitter kein start server in application
"""

INIT_BRIDGE = """
(function() {
    new QWebChannel(qt.webChannelTransport, function(channel) {
        window.qt = channel.objects.qt;
        window.dispatchEvent(new CustomEvent('qtready'));
    });

    function on_mousedown(event) {
        if (event.target.classList.contains("qt-drag")) {
            window.qt.start_window_drag();
            return;
        }

        var d;
        for(d of ["n", "ne", "e", "se", "s", "sw", "w", "nw"]) {
            if (event.target.classList.contains("qt-size-"+d)) {
                window.qt.start_window_size(d);
                return;
            }
        }
    }

    var body = document.querySelector("body");
    body.addEventListener("mousedown", on_mousedown);
})()
"""

MAXIMIZED = """
(function() {
    document.querySelector("body").classList.add("maximized");
    var tbar = document.querySelector(".titlebar");
    if (tbar) tbar.classList.add("fullscreen");
})()
"""

NORMAL = """
(function() {
    document.querySelector("body").classList.remove("maximized");
    var tbar = document.querySelector(".titlebar");
    if (tbar) tbar.classList.remove("fullscreen");
})()
"""

FIXED_SIZE = """
document.querySelector("body").classList.add("fixed-size");
"""

NO_HTML_TITLE = """
document.querySelector("body").classList.add("no-html-title");
"""


class JSBridge(QObject):
    def __init__(self, window):
        super().__init__()
        self.window = window

    @Slot()
    def start_window_drag(self):
        self.window.view.start_window_drag()

    @Slot(str)
    def start_window_size(self, direction):
        self.window.view.start_window_size(direction)

    @Slot(int, int)
    def set_minsize(self, width, height):
        self.window.setMinimumSize(width, height)

    @Slot(int, int)
    def set_size(self, width, height):
        self.window.resize(width, height)

    @Slot(int, int)
    def set_fixedsize(self, width, height):
        self.window.setFixedSize(width, height)
        self.window.size_is_fixed = True
        self.window.view.page().runJavaScript(FIXED_SIZE)

    @Slot()
    def close(self):
        self.window.close()

    @Slot()
    def maximize(self):
        self.window.showNormal()

    @Slot()
    def minimize(self):
        self.window.showMinimized()

    @Slot()
    def fullscreen(self):
        self.window.showFullScreen()

    @Slot(str, QJsonValue, result=str)
    def call(self, func_name, param):
        print("call", func_name, param, param.toObject())
        return "eins"

    @Slot(str)
    def receiveText(self, text):
        print("receiveText", text)


class WindowDragging:
    drag_pos = drag_width = None

    def __init__(self):
        super().__init__()
        QApplication.instance().installEventFilter(self)
        self.move_function = lambda x: None

    def start_window_drag(self):
        self.drag_pos = self.last_press_pos - self.parent().frameGeometry().topLeft()
        self.drag_width = self.parent().frameGeometry().width()
        self.move_function = self.window_drag
        self.grabMouse()

    def window_drag(self, event):
        if self.drag_pos is not None and event.buttons():
            parent = self.parent()
            if parent.isFullScreen() or parent.isMaximized():
                parent.showNormal()
                return

            drag_pos = QPoint(
                int((self.drag_pos.x() / self.drag_width) * parent.frameGeometry().width()),
                self.drag_pos.y())

            parent.move(event.globalPos() - drag_pos)

    def start_window_size(self, direction):
        self.drag_pos = self.last_press_pos - getattr(self, f"get_dragref_{direction}")()
        self.move_function = getattr(self, f"window_size_{direction}")
        self.grabMouse()

    def get_dragref_n(self):
        return self.parent().frameGeometry().topLeft()

    def get_dragref_nw(self):
        return self.parent().frameGeometry().topLeft()

    def get_dragref_ne(self):
        return self.parent().frameGeometry().topRight()

    def get_dragref_w(self):
        return self.parent().frameGeometry().topLeft()

    def get_dragref_s(self):
        return self.parent().frameGeometry().bottomLeft()

    def get_dragref_sw(self):
        return self.parent().frameGeometry().bottomLeft()

    def get_dragref_se(self):
        return self.parent().frameGeometry().bottomRight()

    def get_dragref_e(self):
        return self.parent().frameGeometry().topRight()

    def window_size_n(self, event):
        if self.drag_pos is not None and event.buttons():
            parent = self.parent()
            geometry = parent.frameGeometry()
            geometry.setTop((event.globalPos() - self.drag_pos).y())
            parent.setGeometry(geometry)

    def window_size_nw(self, event):
        if self.drag_pos is not None and event.buttons():
            parent = self.parent()
            geometry = parent.frameGeometry()
            geometry.setTopLeft(event.globalPos() - self.drag_pos)
            parent.setGeometry(geometry)

    def window_size_ne(self, event):
        if self.drag_pos is not None and event.buttons():
            parent = self.parent()
            geometry = parent.frameGeometry()
            geometry.setTopRight(event.globalPos() - self.drag_pos)
            parent.setGeometry(geometry)

    def window_size_s(self, event):
        if self.drag_pos is not None and event.buttons():
            parent = self.parent()
            geometry = parent.frameGeometry()
            geometry.setBottom((event.globalPos() - self.drag_pos).y())
            parent.setGeometry(geometry)

    def window_size_se(self, event):
        if self.drag_pos is not None and event.buttons():
            parent = self.parent()
            geometry = parent.frameGeometry()
            geometry.setBottomRight(event.globalPos() - self.drag_pos)
            parent.setGeometry(geometry)

    def window_size_sw(self, event):
        if self.drag_pos is not None and event.buttons():
            parent = self.parent()
            geometry = parent.frameGeometry()
            geometry.setBottomLeft(event.globalPos() - self.drag_pos)
            parent.setGeometry(geometry)

    def window_size_e(self, event):
        if self.drag_pos is not None and event.buttons():
            parent = self.parent()
            geometry = parent.frameGeometry()
            geometry.setRight((event.globalPos() - self.drag_pos).x())
            parent.setGeometry(geometry)

    def window_size_w(self, event):
        if self.drag_pos is not None and event.buttons():
            parent = self.parent()
            geometry = parent.frameGeometry()
            geometry.setLeft((event.globalPos() - self.drag_pos).x())
            parent.setGeometry(geometry)

    def mousePressEvent(self, event):
        self.last_press_pos = event.globalPos()
        self.delta_br = None

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.drag_pos is not None:
            self.drag_pos = self.drag_width = None
            self.releaseMouse()
            self.move_function = lambda x: None

    def mouseMoveEvent(self, event):
        self.move_function(event)

    def eventFilter(self, object, event):
        if object.parent() == self:
            if event.type() == QEvent.MouseMove:
                self.mouseMoveEvent(event)
            elif event.type() == QEvent.MouseButtonPress:
                self.mousePressEvent(event)
            elif event.type() == QEvent.MouseButtonRelease:
                self.mouseReleaseEvent(event)

        return False


class WebView(WindowDragging, QWebEngineView):
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        inspect_element = QAction('Inspect Element', menu)
        inspect_element.triggered.connect(self.show_inspector)
        menu.addAction(inspect_element)
        menu.exec_(event.globalPos())

    # Create a new webview window pointing at the Remote debugger server
    def show_inspector(self):
        wid = self.parent().wid + '-inspector'
        try:
            # If inspector already exists, bring it to the front
            BrowserWindow.instances[wid].raise_()
            BrowserWindow.instances[wid].activateWindow()
        except KeyError:
            from .debug import Inspector
            inspector = Inspector(wid, self.page(), BrowserWindow.instances)
            inspector.show()


class NavigationHandler(QWebEnginePage):
    def acceptNavigationRequest(self, url, type, is_main_frame):
        # webbrowser.open(url.toString(), 2, True)
        print("acceptNavigationRequest", url)
        return False


class WebPage(QWebEnginePage):
    def __init__(self):
        super().__init__()
        self.featurePermissionRequested.connect(self.on_feature_permission_requested)
        self.iconChanged.connect(self.on_icon_changed)
        self.nav_handler = NavigationHandler(self)

    def on_feature_permission_requested(self, url, feature):
        self.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)

    def on_icon_changed(self, icon):
        print("icon changed", icon, self.parent())

    def createWindow(self, type):
        return self.nav_handler


class BrowserWindow(QMainWindow):
    instances = {}
    size_is_fixed = False

    def __init__(self, wid, url, config):
        super().__init__()
        self.wid = wid
        self.instances[wid] = self

        self.setWindowTitle('Larch Bo Browser')
        self.view = WebView()
        self.view.setPage(WebPage())

        self.init_by_config(config)
        self.view.page().loadFinished.connect(self.on_load_finished)

        self.setCentralWidget(self.view)

        self.channel = QWebChannel(self.view.page())
        self.view.page().setWebChannel(self.channel)

        self.view.load(QUrl(url))
        self.view.page().titleChanged.connect(self.setWindowTitle)

    def init_by_config(self, config):
        args = config["args"]
        wconfig = config.get("window", {})

        flags = self.windowFlags()
        if wconfig.get("frameless", True):
            flags = flags | Qt.FramelessWindowHint

        if wconfig.get("ontop"):
            flags = flags | Qt.WindowStaysOnTopHint

        self.setWindowFlags(flags)

        if wconfig.get("transparent"):
            self.background_color = QColor('transparent')
            palette = self.palette()
            palette.setColor(self.backgroundRole(), self.background_color)
            self.setPalette(palette)
            # Enable the transparency hint
            self.setAttribute(Qt.WA_TranslucentBackground)

            self.view.setAttribute(Qt.WA_TranslucentBackground)
            self.view.setAttribute(Qt.WA_OpaquePaintEvent, False)
            self.view.setStyleSheet("background: transparent;")

            self.view.page().setBackgroundColor(Qt.transparent)

        availableGeometry = self.screen().availableGeometry()
        if args.width:
            width = args.width
        else:
            width = wconfig.get("width", availableGeometry.width() // 2)

        if args.height:
            height = args.height
        else:
            height = wconfig.get("height", availableGeometry.height() // 2)

        if wconfig.get("fixedsize"):
            self.setFixedSize(width, height)
            self.size_is_fixed = True
        else:
            self.resize(width, height)

        if args.left:
            left = args.left
        else:
            left = wconfig.get("left", (availableGeometry.width() - width) // 2)

        if args.top:
            top = args.top
        else:
            top = wconfig.get("top", (availableGeometry.height() - height) // 2)

        self.move(left, top)

        if not config.get("debug"):
            self.view.setContextMenuPolicy(Qt.NoContextMenu)

    def closeEvent(self, event):
        self.instances.pop(self.wid, None)
        event.accept()
        if not self.instances:
            QApplication.instance().exit()

    def on_load_finished(self):
        if self.wid.endswith("-inspector"):
            return

        self._set_js_api()

    def _set_js_api(self):
        qwebchannel_js = QFile('://qtwebchannel/qwebchannel.js')
        if qwebchannel_js.open(QFile.ReadOnly):
            source = bytes(qwebchannel_js.readAll()).decode('utf-8')
            qwebchannel_js.close()
            self.view.page().runJavaScript(source)
            self.js_bridge = JSBridge(self)
            self.channel.registerObject('qt', self.js_bridge)
            self.view.page().runJavaScript(INIT_BRIDGE)
            if self.size_is_fixed:
                self.view.page().runJavaScript(FIXED_SIZE)

            if not self.windowFlags() & Qt.FramelessWindowHint:
                self.view.page().runJavaScript(NO_HTML_TITLE)

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            if self.isMaximized() or self.isFullScreen():
                self.view.page().runJavaScript(MAXIMIZED)
            else:
                self.view.page().runJavaScript(NORMAL)

        return False


class LocalRedirector(QWebEngineUrlRequestInterceptor):
    def __init__(self, resource_path):
        super().__init__()
        self.resource_path = Path(resource_path)

    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        if url.startswith("http://localhost:"):
            path = url[17:].split("/", 1)[-1]
            if path and not path.startswith("api"):
                new_url = QUrl.fromLocalFile(str(self.resource_path/path))
                print("load", new_url, (self.resource_path/path).exists())
                try:
                    info.redirect(new_url)
                except Exception as e:
                    print("error", e)


def start_frontend(url, config):
    argv = sys.argv[:]
    if "--disable-web-security" not in sys.argv:
        argv.append("--disable-web-security")

    app = QApplication(argv)
    logger.info("start main window with url %r", url)
    # redirector = LocalRedirector(config["resources_path"])
    # QWebEngineProfile.defaultProfile().setUrlRequestInterceptor(redirector)
    mainWin = BrowserWindow("main", url, config)
    mainWin.show()
    return app.exec()
