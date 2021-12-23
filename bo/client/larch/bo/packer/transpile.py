import re
import subprocess
import logging
import json
import shutil
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

    copy_resources(linker)


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


def copy_resources(linker):
    data = read_project_file(linker)
    linker.context["python_sources"] = set(m["source"] for m in data["modules"])
    linker.context["resources"] = resources = set()
    for m in data["modules"]:
        spath = Path(m["source"])
        with open(spath, "r") as f:
            source = f.read()

        dirpath = spath.parent
        for found in require_replace.finditer(source):
            require = found.group(1)
            require_path = dirpath/require
            if not require_path.exists():
                # a global package
                continue

            dest_path = linker.path/require
            resources.add(str(require_path))
            if not dest_path.exists() or require_path.stat().st_mtime > dest_path.stat().st_mtime:
                shutil.copy(require_path, dest_path)


def watch(linker, wait_for_change):
    while True:
        copy_resources(linker)
        sources = linker.context["python_sources"] | linker.context["resources"]
        wait_for_change(sources)
        transpile(linker)
