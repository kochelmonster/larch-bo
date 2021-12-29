"""
larch browser objects pyside based standalone applications.
"""
from setuptools import setup, find_packages


dependencies = [
    "larch-browser-objects-server"]


setup(
    name='larch-browser-objects-qt-application',
    version="0.0.1",
    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    packages=find_packages(),
    install_requires=dependencies,
    namespace_packages=['larch', "larch.bo"],

    # metadata for upload to PyPI
    author='Michael Reithinger',
    author_email='mreithinger@web.de',
    description='A transcrypt react ui library, pyside based standalone application',
    license='GNU',
    keywords='library',
    url='http://example.com/larch-bo/',   # project home page, if any
    )
