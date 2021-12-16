"""interface to webpack manager"""
import re
import json
import subprocess
import logging
import signal
from pathlib import Path
from .npm import make as npm_make

logger = logging.getLogger("larch.bo.packer")

DIR = Path(__file__).resolve().parent

NEEDED_PACKAGES = """
parcel
"""

require_replace = re.compile("require.*\"(.*?)\"")


def init(config):
    start = Path(config["root"]).parent
    packages = NEEDED_PACKAGES.strip().split()
    for p in packages:
        logger.debug("init package %r", p)
        npm_make(p, start)


def make_package_json(linker):
    if "python_aliases" in linker.context:
        template = "package.json"
        template = linker.config.get("parcel_config", DIR/template)
        if Path(template).exists():
            with open(template, "r") as f:
                template = f.read()

        package = json.loads(template)
        package["name"] = linker.config.get("name", Path(linker.config["root"]).name)
        package["alias"] = linker.context["python_aliases"]

        with open(linker.path/"package.json", "w") as f:
            f.write(json.dumps(package, indent=2))
        return True
    return False


def make(linker):
    logger.info("make parcel %r\n%r", linker.path, linker.config)

    make_package_json(linker)
    # name = linker.path/Path(linker.config["root"]).name.replace(".py", ".js")
    name = linker.path/"index.html"
    cmd = (f'npx parcel build {name} --dist-dir {linker.config["resources_path"]} '
           '--log-level=verbose')
    cmd = f'npx parcel build {name} --dist-dir {linker.config["resources_path"]}'
    if linker.config.get("debug"):
        cmd += " --no-optimize"

    result = subprocess.run(
        cmd, shell=True, cwd=linker.path, stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE, encoding="utf8")

    print(cmd)
    print(result.stdout)
    if result.returncode:
        raise RuntimeError("Error completing bundler")


def watch(linker):
    build_path = linker.config["build_path"]
    name = linker.path/"index.html"
    cmd = (f'npx parcel watch {name} --dist-dir {linker.config["resources_path"]} '
           '--no-hmr --log-level=verbose')
    try:
        process = subprocess.Popen(cmd, shell=True, cwd=build_path)
        process.wait()
        print("done parcel", process.returncode)
        signal.raise_signal(signal.SIGINT)
    finally:
        process.kill()
