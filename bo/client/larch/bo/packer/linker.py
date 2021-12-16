"""links resources to a single tar file"""
from pathlib import Path
from shutil import rmtree


class Linker:
    def __init__(self, config, force, remove):
        self.path = Path(config.get("build_path") or Path.cwd().resolve()/".lfrontend")
        # remove = False
        if remove:
            rmtree(self.path, ignore_errors=True)

        self.path.mkdir(parents=True, exist_ok=True)
        self.force = force
        self.config = config
        self.context = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.compress()

    def compress(self):
        pass
