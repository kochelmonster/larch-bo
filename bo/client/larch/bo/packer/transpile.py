import os
import re
import subprocess
import logging
import json
from pathlib import Path

logger = logging.getLogger("larch.bo.packer")

require_replace = re.compile("require.*\"(.*?)\"")


def needs_transpile(linker):
    if linker.force:
        return True

    try:
        with open(linker.path/"dist/manifest.json", "r") as f:
            manifest = json.load(f)

        sources = manifest["python_sources"]
    except Exception:
        return True

    linker.context["python_sources"] = set(sources.keys())
    return any(Path(source).stat().st_mtime > mtime for source, mtime in sources.items())


def additional_directories():
    dirs = []
    try:
        # workaround for transcrypt
        import larch.lib.adapter
        dirs.append(str(Path(larch.lib.adapter.__file__).parents[2]))
    except ImportError:
        pass
    return dirs


def transpile(linker):
    logger.info("transpile python %r\n%r", linker.path, linker.config)
    cmd = f'python -m transcrypt --nomin --map --verbose -od {linker.path} {linker.config["root"]}'

    dirs = list(linker.config.get("extra_search_path", [])) + additional_directories()
    if dirs:
        dirs = "$".join(d.replace(" ", "#") for d in dirs)
        cmd += f" -xp {dirs}"

    print(cmd)
    result = subprocess.run(
        cmd, shell=True, cwd=linker.path, stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE, encoding="utf8")
    print(result.stdout)
    return result.returncode


def make(linker):
    if not needs_transpile(linker):
        return

    if transpile(linker):
        raise RuntimeError("Error transpiling")

    build_aliases(linker)


def extend_manifest(linker):
    try:
        with open(linker.path/"dist/manifest.json", "r") as f:
            manifest = json.load(f)
    except IOError:
        manifest = {}

    manifest["python_sources"] = python_sources = {}
    for source in linker.context["python_sources"]:
        python_sources[source] = Path(source).stat().st_mtime

    with open(linker.path/"dist/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)


def get_project_file(linker):
    name = Path(linker.config["root"]).stem + ".project"
    return linker.path/name


def read_project_file(linker):
    with open(get_project_file(linker), "rb") as f:
        return json.load(f)


def build_aliases(linker):
    data = read_project_file(linker)
    linker.context["python_sources"] = set(m["source"] for m in data["modules"])
    linker.context["python_aliases"] = aliases = {}
    for m in data["modules"]:
        spath = Path(m["source"])
        with open(spath, "r") as f:
            source = f.read()

        dirpath = spath.parent
        for found in require_replace.finditer(source):
            require = found.group(1)
            dstpath = os.path.relpath(str(dirpath/require), str(spath))
            aliases[require] = str(dstpath)


def watch(linker, wait_for_change):
    while True:
        build_aliases(linker)
        sources = linker.context["python_sources"]
        wait_for_change(sources)
        transpile(linker)
