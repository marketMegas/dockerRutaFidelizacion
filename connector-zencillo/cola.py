import json
import os
from pathlib import Path

COLA = Path(os.getenv("COLA_ARCHIVO", "cola_offline.json"))


def cargar():
    if not COLA.exists():
        return []
    try:
        return json.loads(COLA.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def guardar(items):
    COLA.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def encolar(venta):
    items = cargar()
    if any(v.get("id_externo") == venta.get("id_externo") for v in items):
        return False
    items.append(venta)
    guardar(items)
    return True


def quitar(id_externo):
    items = [v for v in cargar() if v.get("id_externo") != id_externo]
    guardar(items)


def pendientes():
    return cargar()
