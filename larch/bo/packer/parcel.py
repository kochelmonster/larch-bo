"""interface to webpack manager"""
import re
import os
import sys
import json
import logging
import signal
from pickle import loads, dumps
from pathlib import Path
from larch.lib.utils import deep_update
from gevent import spawn, subprocess
from .npm import make as npm_make

logger = logging.getLogger("larch.bo.packer")

DIR = Path(__file__).resolve().parent

NEEDED_PACKAGES = {"parcel"}


require_replace = re.compile("require.*\"(.*?)\"")
source_map_comment = re.compile(r"\n?//# sourceMappingURL=.*$")


QT_BROWSER = {
    # "browserslist": "Chrome 80"
    "browserslist": "> 0.5%, last 2 versions, not dead",
}

INTERNET = {
    "browserslist": "> 0.5%, last 2 versions, not dead"
}


PACKAGE_TEMPLATE = {
    "devDependencies": {
        "parcel": "latest"
    },
    "source": ""
}


def split_package_spec(spec):
    if spec.startswith("@"):
        if spec.count("@") > 1:
            package, version = spec.rsplit("@", 1)
            return package, version
        return spec, "latest"

    if "@" in spec:
        package, version = spec.rsplit("@", 1)
        return package, version

    return spec, "latest"


def make_dependencies():
    deps = {}
    for spec in sorted(NEEDED_PACKAGES):
        package, version = split_package_spec(spec)
        if package != "parcel":
            deps[package] = version
    return deps


def init(config):
    start = Path(config["root"]).parent
    for p in NEEDED_PACKAGES:
        logger.debug("init package %r", p)
        npm_make(p, start)

    if config.get("transmitter"):
        npm_make("msgpack-lite", start)


def make_package_json(linker, directory, entry):
    package = loads(dumps(PACKAGE_TEMPLATE))  # deep copy
    dependencies = make_dependencies()
    if dependencies:
        package["dependencies"] = dependencies

    if linker.config.get("window"):
        # standalone
        package = deep_update(package, QT_BROWSER)
    else:
        package = deep_update(package, INTERNET)

    package["source"] = entry
    package = deep_update(package, linker.config.get("parcel_config", {}))

    with open(linker.path/directory/"package.json", "w") as f:
        f.write(json.dumps(package, indent=2))


def patch_msgpack(script):
    """
    msgpack-lite does not work well with parcel == we have to patch the output
    """
    script.write_text(script.read_text().replace(".global", ".$parcel$global"))


def create_entries(linker):
    entry_paths = []
    entry_paths.append(linker.trans_path/"index.html")
    if linker.transmitter:
        entry_paths.append(linker.path/"transmitter")

    return entry_paths


def strip_transcrypt_sourcemaps(path):
    if not path.exists():
        return

    for file in path.iterdir():
        if file.suffix == ".map":
            file.unlink()
            continue

        if file.suffix != ".js":
            continue

        code = file.read_text()
        patched = source_map_comment.sub("", code)
        if patched != code:
            file.write_text(patched)


def should_emit_source_maps(config):
    return bool(config.get("debug") or config.get("source_map"))


def dist_has_source_maps(config):
    dist_path = Path(config["resource_path"])
    if not dist_path.exists():
        return False
    return any(dist_path.glob("*.map"))


def make(linker):
    logger.info("make parcel %r\n%r", linker.path, linker.config)

    emit_source_maps = should_emit_source_maps(linker.config)

    if not emit_source_maps:
        strip_transcrypt_sourcemaps(linker.trans_path)
        if linker.transmitter:
            strip_transcrypt_sourcemaps(linker.path/"transmitter")

    main_name = Path(linker.config["root"]).with_suffix(".js")
    make_package_json(linker, "main", main_name.name)
    if linker.transmitter:
        make_package_json(linker, "transmitter", linker.transmitter)

    environ = os.environ.copy()
    environ["FORCE_COLOR"] = "3"
    for entry in create_entries(linker):
        cmd = (f'npx parcel build {entry} --dist-dir {linker.config["resource_path"]}'
               f' --cache-dir {linker.config["build_path"]/".parcel-cache"}'
               ' --public-url ./')
        if not emit_source_maps:
            cmd += " --no-source-maps"
        if linker.config.get("debug"):
            cmd += " --no-optimize"

        result = subprocess.run(
            cmd, shell=True, cwd=entry.parent, stderr=subprocess.STDOUT, env=environ,
            stdout=subprocess.PIPE, encoding="utf8")

        print(cmd)
        for line in result.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
        if result.returncode:
            raise RuntimeError("Error completing bundler")

    if linker.transmitter:
        patch_msgpack(linker.config["resource_path"]/linker.transmitter)

    try:
        classic = linker.config["args"].classic
    except (AttributeError, KeyError):
        classic = False

    if classic:
        make_strict(linker)


def make_strict(linker):
    """add use strict to the main output"""
    for f in linker.config["resource_path"].iterdir():
        if f.suffix == ".js":
            print("make strict", f)
            js = f.read_text()
            if not js.startswith("'use strict'"):
                f.write_text("'use strict';\n" + js)
