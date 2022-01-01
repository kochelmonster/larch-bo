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


def init(config):
    start = Path(config["root"]).parent
    for p in NEEDED_PACKAGES:
        logger.debug("init package %r", p)
        npm_make(p, start)


def make_package_json(linker, directory, entry):
    package = loads(dumps(PACKAGE_TEMPLATE))  # deep copy

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

    entry_paths.append(linker.path/"main")
    if linker.transmitter:
        entry_paths.append(linker.path/"transmitter")

    return entry_paths


def make(linker):
    logger.info("make parcel %r\n%r", linker.path, linker.config)

    main_name = Path(linker.config["root"]).with_suffix(".js")
    make_package_json(linker, "main", main_name.name)
    if linker.transmitter:
        make_package_json(linker, "transmitter", linker.transmitter)

    environ = os.environ.copy()
    environ["FORCE_COLOR"] = "3"

    for entry in create_entries(linker):
        cmd = f'npx parcel build {entry} --dist-dir {linker.config["resource_path"]}'
        cmd += " --no-content-hash"
        if linker.config.get("debug"):
            cmd += " --no-optimize"

        result = subprocess.run(
            cmd, shell=True, cwd=linker.path, stderr=subprocess.STDOUT, env=environ,
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


def watch(linker):
    environ = os.environ.copy()
    environ["FORCE_COLOR"] = "3"
    build_path = linker.config["build_path"]
    entry = create_entries(linker)[0]
    cmd = (f'npx parcel watch {entry} --dist-dir {linker.config["resource_path"]} '
           '--no-hmr --log-level=verbose --watch-for-stdin')
    try:
        print("**start parcel watch")
        process = subprocess.Popen(
            cmd, shell=True, cwd=build_path, env=environ, stdin=subprocess.PIPE)
        process.wait()
        print("done parcel", process.returncode)
        signal.raise_signal(signal.SIGINT)
    finally:
        process.stdin.close()
        process.kill()


def start_watcher(linker, wait_for_change):
    main_name = Path(linker.config["root"]).with_suffix(".js")
    make_package_json(linker, "main", main_name.name)
    if linker.transmitter:
        make_package_json(linker, "transmitter", linker.transmitter)

    respath = linker.config["resource_path"]
    if linker.transmitter and not (respath/linker.transmitter).exists():
        make(linker)

    return [spawn(watch, linker)]
