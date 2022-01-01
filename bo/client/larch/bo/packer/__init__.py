from . import parcel, gettext, transpile, html, linker


def compile_resources(config, force):
    parcel.init(config)
    with linker.Linker(config, force) as linker_:
        if transpile.make(linker_):  # all done
            return linker_
        parcel.make(linker_)
        gettext.make(linker_)
        transpile.extend_manifest(linker_)
        html.make(linker_)
    return linker_


def start_watcher(config, wait_for_change):
    respath = config["resource_path"]
    index_html = respath/"index.html"
    if not index_html.exists():
        linker_ = compile_resources(config, False)
    else:
        parcel.init(config)
        linker_ = linker.Linker(config, False)
        transpile.make(linker_)
        transpile.extend_manifest(linker_)

    return [transpile.start_watcher(linker_, wait_for_change), parcel.start_watcher(linker_)]
