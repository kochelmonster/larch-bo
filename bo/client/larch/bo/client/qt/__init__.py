"""
Simulation of plattform window, in standard alone browser.
"""
# __pragma__("skip")
from larch.bo.packer import parcel
parcel.NEEDED_PACKAGES.extend([
    "electron-titlebar-windows", "titlebar"])
document = None
window = None
def require(p): pass
def __pragma__(*args): pass
def create_titlebar(): pass
def parseFloat(): pass
# __pragma__("noskip")


require("./larch.bo.client.qt.scss")


def on_close():
    if window.qt:
        window.qt.close()


def on_minimize():
    if window.qt:
        window.qt.minimize()


def on_maximize():
    if window.qt:
        window.qt.maximize()


def on_fullscreen():
    if window.qt:
        window.qt.fullscreen()


__pragma__("ifdef", "darwin")
__pragma__('js', '{}', '''

const TitleBar = require("titlebar");

function create_titlebar(container, fullscreen) {
    var titlebar = new TitleBar({draggable: false});
    titlebar.appendTo(container);
    return titlebar;
}
''')
__pragma__("else")
__pragma__('js', '{}', '''

const ElectronTitlebarWindows = require('electron-titlebar-windows');

function create_titlebar(container, fullscreen) {
    var titlebar = new ElectronTitlebarWindows({fullscreen: fullscreen});
    titlebar.on("close", on_close);
    titlebar.on("minimize", on_minimize);
    titlebar.on("maximize", on_maximize);
    titlebar.on("fullscreen", on_fullscreen);
    titlebar.titlebarElement.classList.add("qt-drag");
    titlebar.appendTo(container);
    return titlebar;
}

''')
__pragma__("endif")


WINDOW = """
<div class="window-left">
    <div class="qt-size-nw"></div>
    <div class="qt-size-w"></div>
    <div class="qt-size-sw"></div>
</div>
<div class="window-right">
    <div class="qt-size-ne"></div>
    <div class="qt-size-e"></div>
    <div class="qt-size-se"></div>
</div>
<div class="window-top">
    <div class="qt-size-nw"></div>
    <div class="qt-size-n"></div>
    <div class="qt-size-ne"></div>
</div>
<div class="window-bottom">
    <div class="qt-size-sw"></div>
    <div class="qt-size-s"></div>
    <div class="qt-size-se"></div>
</div>
<div class="window">
</div>
"""


def create_window_container(parent, fullscreen=False):
    parent.innerHTML = WINDOW
    container = parent.querySelector(".window")
    create_titlebar(container, fullscreen)
    content = document.createElement("div")
    content.classList.add("window-content")
    container.appendChild(content)
    return content


def get_title():
    return document.querySelector(".titlebar")


def calc_minsize():
    body = document.querySelector("body")
    body.classList.add("calc-min-size")
    container = body.querySelector(".window")
    style = window.getComputedStyle(container)
    width = parseFloat(style.marginLeft) + parseFloat(style.width) + parseFloat(style.marginRight)
    height = parseFloat(style.marginTop) + parseFloat(style.height) + parseFloat(style.marginBottom)
    body.classList.remove("calc-min-size")
    return [int(width+0.5), int(height+0.5)]
