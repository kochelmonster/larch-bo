# README for larch-bo unified package

This package combines the client, server, and qt-application components into a single Python package under the `larch` namespace.

## Structure
- larch/bo/client/      ← from client/larch/bo/client/
- larch/bo/packer/      ← from client/larch/bo/packer/
- larch/bo/server/      ← from server/larch/bo/server/
- larch/bo/api/         ← from server/larch/bo/api/
- larch/bo/qt/          ← from qt-application/larch/bo/qt/

## Installation

```sh
pip install -e .
```

## Development
- Add shared dependencies to `requirements.txt`.
- Add package metadata to `pyproject.toml`.
