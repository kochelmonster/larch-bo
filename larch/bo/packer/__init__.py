from . import parcel, gettext, transpile, html, linker
from gevent import spawn

def compile_resources(config, force):
    parcel.init(config)
    with linker.Linker(config, force) as linker_:
        if transpile.make(linker_):  # all done
            return linker_
        html.make(linker_)
        parcel.make(linker_)
        gettext.make(linker_)
        transpile.extend_manifest(linker_)
        
    return linker_


def start_watcher(config, wait_for_change):
    def watch():
        while True:
            sources = linker_.context["python_sources"] | linker_.context["resources"]
            changed = wait_for_change(sources)
            compile_resources(config, not changed.endswith(".py"))

    linker_ = compile_resources(config, False)
    if "resources" not in linker_.context:
        transpile.copy_resources(linker_)

    return [spawn(watch)]
