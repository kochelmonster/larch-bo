"""
larch browser objects server package.
"""
from setuptools import setup, find_namespace_packages


dependencies = [
    "gevent",
    'Werkzeug>=0.8.3',
    'msgpack',
    "gevent-websocket @ git+https://gitlab.com/noppo/gevent-websocket.git",
    "watchdog_gevent"]


setup(
    name='larch-browser-objects-server',
    version="0.0.1",
    install_requires=dependencies,
    packages=find_namespace_packages(where="./", include=["larch.bo", "larch.bo.api", "larch.bo.server"]),

    # metadata for upload to PyPI
    author='Michael Reithinger',
    author_email='mreithinger@web.de',
    description='A transcrypt react ui library, server components',
    license='GNU',
    keywords='library',
    url='https://github.com/kochelmonster/larch-bo',   # project home page, if any
    )
