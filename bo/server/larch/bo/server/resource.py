"""A resource manager
"""
import logging
from gettext import GNUTranslations
from pathlib import Path
from werkzeug.exceptions import NotFound

logger = logging.getLogger('larch.ui.resource')


# resource handler
# ------------------------------
class ResourceManager:
    """
    A global resource manager, to register Resources and
    handle Resource requests
    """

    def __init__(self, config):
        self.config = config
        self.path = Path(config["resources_path"])

    def shutdown(self):
        pass

    def open_resource(self, name):
        """open as a file like object"""
        try:
            return open(self.path/name)
        except KeyError:
            raise NotFound(name)

    def load_resource(self, name):
        try:
            return (self.path/name).read_bytes()
        except IOError:
            try:
                if self.config["debug"] and (name.endswith(".py") or name.endswith(".js")):
                    return (Path.home()/name).read_bytes()
            except IOError:
                pass
        raise NotFound(name)

    def load_catalog(self, language, fallback):
        lines = to_str(self.load_resource("i18n/map")).split()
        lines = (i.split(":") for i in lines)
        lmap = {k: v.split(",") for k, v in lines}

        best_fit = lmap.get(language, ())
        fit = lmap.get(language.split("-")[0]) if "-" in language else ()

        def create_catalog(paths, fallback):
            for path in paths:
                f = self.open_resource(path)
                try:
                    catalog = GNUTranslations(f)
                    catalog.add_fallback(fallback)
                    fallback = catalog
                finally:
                    f.close()
            return fallback

        if best_fit or fit:
            catalog = create_catalog(fit, fallback)
            return create_catalog(best_fit, catalog)

        return None
