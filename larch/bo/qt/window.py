"""Standalone Browser for larch browser object"""
import logging
from PySide6.QtCore import QUrl, Qt, QEvent, QFile, QObject, Slot, QPoint
from PySide6.QtGui import QColor, QAction
from PySide6.QtWidgets import QMainWindow, QMenu, QApplication
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel


logger = logging.getLogger('larch.bo.qt')


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
})();
document.querySelector("body").classList.add("qt-app");
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

    @Slot(str)
    def set_background(self, color):
        self.window.set_background(color)

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

    @Slot()
    def start_debugger(self):
        self.window.view.show_inspector()

    @Slot()
    def reload(self):
        self.window.reload()

    @Slot(str, str, str, result=list)
    def choose_files(self, mode, suggest, mimes):
        mode = {
            "file": QWebEnginePage.FileSelectOpen,
            "multi": QWebEnginePage.FileSelectOpenMultiple,
            "folder": QWebEnginePage.FileSelectUploadFolder
        }[mode]
        print("choose files called")
        return self.window.view.page().chooseFiles(mode, [suggest], [])


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
        try:
            self.inspector
        except AttributeError:
            def remove(): del self.inspector
            from .debug import Inspector
            self.inspector = Inspector(self.page())
            self.inspector.show()
            self.inspector.closed.connect(remove)


class WebPage(QWebEnginePage):
    def __init__(self, profile, parent):
        super().__init__(profile, parent)
        self.featurePermissionRequested.connect(self.on_feature_permission_requested)
        self.newWindowRequested.connect(self.on_new_window)

        settings = self.settings()
        settings.setAttribute(settings.JavascriptCanOpenWindows, True)
        settings.setAttribute(settings.AllowWindowActivationFromJavaScript, True)

    def on_feature_permission_requested(self, url, feature):
        print("**feature permission requested")
        self.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)

    def on_new_window(self, request):
        src_window = self.parent().parent()
        window = BrowserWindow(None, src_window.config)
        sgeo = request.requestedGeometry()
        dgeo = window.frameGeometry()
        if v := sgeo.left():
            dgeo.setLeft(v)
        if v := sgeo.right():
            dgeo.setRight(v)
        if v := sgeo.width():
            dgeo.setWidth(v)
        if v := sgeo.height():
            dgeo.setHeight(v)
        window.setGeometry(dgeo)

        if request.destination() == request.DestinationType.InNewDialog:
            window.setWindowModality(Qt.ApplicationModal)

        request.openIn(window.view.page())

    def chooseFiles(self, mode, old, mimes):
        result = super().chooseFiles(mode, old, mimes)
        print("chooseFiles", mode, old, mimes)
        print("result", result)
        return result


class BrowserWindow(QMainWindow):
    instances = set()
    size_is_fixed = False

    def __init__(self, url, config):
        super().__init__()
        self.config = config
        self.instances.add(self)

        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("QT LarchBo Browser")

        self.setWindowTitle('Larch Bo Browser')
        self.view = WebView()
        page = WebPage(profile, self.view)
        self.view.setPage(page)

        self.init_by_config(config)
        page.loadFinished.connect(self.on_load_finished)

        self.setCentralWidget(self.view)

        self.channel = QWebChannel(page)
        page.setWebChannel(self.channel)
        self.js_bridge = JSBridge(self)
        self.channel.registerObject('qt', self.js_bridge)

        page.titleChanged.connect(self.setWindowTitle)
        page.iconChanged.connect(self.setWindowIcon)

        if url:
            self.view.load(QUrl(url))

    def init_by_config(self, config):
        args = config["args"]
        wconfig = config.get("window", {})

        flags = self.windowFlags()
        if wconfig.get("frameless", True) and "window" in config:
            flags = flags | Qt.FramelessWindowHint

        if wconfig.get("ontop"):
            flags = flags | Qt.WindowStaysOnTopHint

        self.setWindowFlags(flags)
        self.set_background(wconfig.get("background", "white"))

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

    def reload(self):
        self.view.page().triggerAction(QWebEnginePage.WebAction.ReloadAndBypassCache)

    def on_load_finished(self):
        self._set_js_api()
        wconfig = self.config.get("window", {})
        if wconfig.get("visible", True):
            self.show()
        if wconfig.get("debugger", False):
            self.view.show_inspector()

    def _set_js_api(self):
        qwebchannel_js = QFile('://qtwebchannel/qwebchannel.js')
        if qwebchannel_js.open(QFile.ReadOnly):
            source = bytes(qwebchannel_js.readAll()).decode('utf-8')
            qwebchannel_js.close()
            self.view.page().runJavaScript(source)
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

    def closeEvent(self, event):
        super().closeEvent(event)
        self.instances.remove(self)

    def set_background(self, background):
        self.background_color = QColor(background)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), self.background_color)
        self.setPalette(palette)
        self.view.setStyleSheet(f"background: {background};")
        if background == "transparent":
            # Enable the transparency hint
            self.setAttribute(Qt.WA_TranslucentBackground)
            self.view.setAttribute(Qt.WA_TranslucentBackground)
            self.view.setAttribute(Qt.WA_OpaquePaintEvent, False)
            self.view.page().setBackgroundColor(Qt.transparent)
        else:
            self.view.page().setBackgroundColor(self.background_color)


def start_frontend(url, config, filewatch=False):
    app = QApplication([])
    logger.info("start main window with url %r", url)
    w = BrowserWindow(url, config)
    w.show()

    if filewatch:
        from .debug import install_watcher
        install_watcher(config, BrowserWindow.instances)

    return app.exec()
