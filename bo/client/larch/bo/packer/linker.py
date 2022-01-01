"""links resources to a single tar file"""
from pathlib import Path
from shutil import rmtree


class Linker:
    def __init__(self, config, force):
        self.path = Path(config.get("build_path") or Path.cwd().resolve()/".lfrontend")
        if force:
            rmtree(self.path, ignore_errors=True)
            assert(not self.path.exists())

        self.path.mkdir(parents=True, exist_ok=True)
        self.force = force
        self.config = config
        self.context = {}
        self.transmitter = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.compress()

    def compress(self):
        pass
