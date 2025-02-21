"""
larch browser objects productive package.
"""
from setuptools import setup, find_namespace_packages


dependencies = ["larch.lib", "larch.reactive"]


setup(
    name='larch-browser-objects-client',
    version="0.0.1",
    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    packages=find_namespace_packages(where="./", include=["larch.bo", "larch.bo.client"]),
    install_requires=dependencies,

    # metadata for upload to PyPI
    author='Michael Reithinger',
    author_email='mreithinger@web.de',
    description='A transcrypt react ui library, client components',
    license='GNU',
    keywords='library',
    url='http://example.com/larch-bo/',   # project home page, if any
    )
