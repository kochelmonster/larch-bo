"""interface to make translation files"""
import logging

logger = logging.getLogger("larch.bo.packer")


def make(linker):
    logger.info("make gettext %r\n%r", linker.path, linker.config)
