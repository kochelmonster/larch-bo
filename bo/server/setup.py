"""
larch browser objects server package.
"""
from setuptools import setup, find_packages


dependencies = [
    "gevent",
    'Werkzeug>=0.8.3',
    'msgpack',
    "gevent-websocket @ git+https://gitlab.com/noppo/gevent-websocket.git",
    "watchdog_gevent"]


setup(
    name='larch-browser-objects-server',
    version="0.0.1",
    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    packages=find_packages(),
    install_requires=dependencies,
    namespace_packages=['larch', "larch.bo"],

    # metadata for upload to PyPI
    author='Michael Reithinger',
    author_email='mreithinger@web.de',
    description='A transcrypt react ui library, server components',
    license='GNU',
    keywords='library',
    url='http://example.com/larch-bo/',   # project home page, if any
    )
