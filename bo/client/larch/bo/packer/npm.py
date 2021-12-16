"""interface to npm"""
import os
import subprocess
from pathlib import Path


def find_node_modules_path(sub_path, start):  # pragma: no cover
    while True:
        sub = start/"node_modules"/sub_path
        if sub.exists():
            return sub
        parent = start.parent
        if parent == start:
            raise ValueError("No sub_path found.", sub_path)
        start = parent


def make(package_name, start=__file__):  # pragma: no cover
    """check if sub_path exists under the node_modules hierachy beginning
    at start. If the sub_path is not found npm is called to install
    package_name.

    Args:
        package_name (str): package_name to install with npm.
        start (str): start path.

    Returns:
        Path: absolute path of sub_path

    Raises:
        ValueError: if sub_path cannot be found after install
    """
    if "->" in package_name:
        package_name, sub_path = package_name.split("->", 1)
    else:
        sub_path = package_name[:1] + package_name[1:].rsplit("@", 1)[0]

    start = Path(start).resolve()

    try:
        return find_node_modules_path(sub_path, start)
    except ValueError:
        pass

    npm_path = os.environ.get("LARCH_NPM", "npm")
    cmd = f"{npm_path} prefix -g"

    try:
        dirname = subprocess.check_output(cmd, shell=True).decode("utf8").strip()
        return find_node_modules_path(sub_path, dirname)
    except Exception:
        pass

    if not start.is_dir():
        start = start.parent

    cmd = f"npm install -D {package_name}"
    print("npm make", cmd)
    subprocess.check_call(cmd, shell=True, cwd=start)
    return find_node_modules_path(sub_path, start)
