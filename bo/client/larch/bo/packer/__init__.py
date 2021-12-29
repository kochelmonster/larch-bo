import threading
from . import parcel, gettext, transpile, html, linker


def compile_resources(config, force):
    parcel.init(config)
    with linker.Linker(config, force) as linker_:
        transpile.make(linker_)
        html.make(linker_)
        parcel.make(linker_)
        gettext.make(linker_)
        transpile.extend_manifest(linker_)
    return linker_


def start_watcher(config, wait_for_change):
    parcel.init(config)
    linker_ = linker.Linker(config, False)
    transpile.make(linker_)
    parcel.make_package_json(linker_)
    transpile.extend_manifest(linker_)

    t = threading.Thread(target=transpile.watch, args=(linker_, wait_for_change))
    t.setDaemon(True)
    t.start()
    t = threading.Thread(target=parcel.watch, args=(linker_,))
    t.setDaemon(True)
    t.start()
