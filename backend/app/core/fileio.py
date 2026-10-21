"""Escritura de archivos fuera del event loop.

write_file se ejecuta con asyncio.to_thread desde código async. Hace el mismo
open/write que antes, pero el disco no bloquea las demás corrutinas.
"""


def write_file(path, mode, *, data, **open_kwargs):
    with open(path, mode, **open_kwargs) as f:
        f.write(data)


def read_file(path, mode, **open_kwargs):
    with open(path, mode, **open_kwargs) as f:
        return f.read()


def read_pickle(path):
    import pickle

    with open(path, "rb") as f:
        return pickle.load(f)


def write_json(path, obj):
    import json

    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
