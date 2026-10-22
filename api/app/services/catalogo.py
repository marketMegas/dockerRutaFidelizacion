"""Catalogo de premios y niveles, respaldado por un archivo JSON.

El archivo es la fuente de verdad y lo edita el panel admin; la API solo lo
lee (y lo escribe cuando el panel guarda cambios). Vive en un volumen Docker
para que sobreviva a los despliegues.

Formato:

    {
      "version": 3,
      "niveles": [
        {"clave": "arranque", "nombre": "Arranque", "minimo": 0,
         "multiplicador": 1.0, "descripcion": "..."}
      ],
      "premios": [
        {"clave": "cafe", "nombre": "Cafe gratis", "descripcion": "...",
         "costo_puntos": 100, "activo": true, "codigos": ["7K3M-92XQ", ...]}
      ]
    }
"""

import json
import logging
import os
import shutil
import tempfile
import threading
from pathlib import Path
from typing import Any

from sqlalchemy import select

from ..config import settings
from ..models import Canje

logger = logging.getLogger(__name__)

ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
LONGITUD_CODIGO = 8
MAX_CODIGOS_POR_PREMIOS = 5000

_lock = threading.RLock()
_cache: dict[str, tuple[int, int, dict]] = {}

RUTA_PLANTILLA = Path(__file__).resolve().parent.parent / "resources" / "catalogo_inicial.json"


class CatalogoInvalido(Exception):
    """El catalogo no cumple el contrato de datos."""


class ConflictoCatalogo(Exception):
    """El catalogo fue modificado por alguien mas mientras se editaba."""

    def __init__(self, version_actual: int) -> None:
        super().__init__("El catalogo cambio en el servidor. Recarga y vuelve a intentar.")
        self.version_actual = version_actual


def invalidar_cache() -> None:
    """Olvida la copia en memoria (lo usa el panel al guardar)."""
    with _lock:
        _cache.clear()


def ruta() -> Path:
    return Path(settings.CATALOGO_PATH)


def normalizar_codigo(valor: Any) -> str | None:
    """Normaliza un codigo a formato XXXX-XXXX. Devuelve None si no es valido."""
    if not isinstance(valor, str):
        return None
    limpio = valor.strip().upper().replace("-", "").replace(" ", "")
    if len(limpio) != LONGITUD_CODIGO:
        return None
    if any(ch not in ALFABETO for ch in limpio):
        return None
    return f"{limpio[:4]}-{limpio[4:]}"


def _catalogo_por_defecto() -> dict:
    try:
        with RUTA_PLANTILLA.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (OSError, json.JSONDecodeError):
        logger.error("No se pudo leer la plantilla del catalogo en %s", RUTA_PLANTILLA)
        return {"version": 1, "niveles": [], "premios": []}
    return datos


def _validar_niveles(niveles: Any) -> list[dict]:
    if not isinstance(niveles, list) or not niveles:
        raise CatalogoInvalido("El catalogo debe tener al menos un nivel.")
    vistos: set[str] = set()
    salida: list[dict] = []
    for posicion, nivel in enumerate(niveles):
        if not isinstance(nivel, dict):
            raise CatalogoInvalido(f"El nivel #{posicion + 1} no es un objeto.")
        clave = str(nivel.get("clave") or "").strip().lower()
        nombre = str(nivel.get("nombre") or "").strip()
        if not clave:
            raise CatalogoInvalido(f"El nivel #{posicion + 1} no tiene clave.")
        if clave in vistos:
            raise CatalogoInvalido(f"Hay dos niveles con la clave '{clave}'.")
        vistos.add(clave)
        if not nombre:
            raise CatalogoInvalido(f"El nivel '{clave}' no tiene nombre.")
        try:
            minimo = float(nivel.get("minimo", 0))
        except (TypeError, ValueError) as exc:
            raise CatalogoInvalido(f"El nivel '{clave}' tiene un minimo no numerico.") from exc
        if minimo < 0:
            raise CatalogoInvalido(f"El nivel '{clave}' no puede tener un minimo negativo.")
        try:
            multiplicador = float(nivel.get("multiplicador", 1))
        except (TypeError, ValueError) as exc:
            raise CatalogoInvalido(f"El nivel '{clave}' tiene un multiplicador no numerico.") from exc
        if multiplicador <= 0:
            raise CatalogoInvalido(f"El nivel '{clave}' necesita un multiplicador mayor que cero.")
        salida.append(
            {
                "clave": clave,
                "nombre": nombre,
                "minimo": minimo,
                "multiplicador": multiplicador,
                "descripcion": str(nivel.get("descripcion") or "").strip(),
            }
        )
    salida.sort(key=lambda n: n["minimo"])
    return salida


def _validar_premios(premios: Any) -> list[dict]:
    if not isinstance(premios, list):
        raise CatalogoInvalido("El catalogo debe tener una lista de premios.")
    vistos: set[str] = set()
    codigos_vistos: set[str] = set()
    salida: list[dict] = []
    for posicion, premio in enumerate(premios):
        if not isinstance(premio, dict):
            raise CatalogoInvalido(f"El premio #{posicion + 1} no es un objeto.")
        clave = str(premio.get("clave") or "").strip().lower()
        nombre = str(premio.get("nombre") or "").strip()
        if not clave:
            raise CatalogoInvalido(f"El premio #{posicion + 1} no tiene clave.")
        if clave in vistos:
            raise CatalogoInvalido(f"Hay dos premios con la clave '{clave}'.")
        vistos.add(clave)
        if not nombre:
            raise CatalogoInvalido(f"El premio '{clave}' no tiene nombre.")
        try:
            costo = int(premio.get("costo_puntos", 0))
        except (TypeError, ValueError) as exc:
            raise CatalogoInvalido(f"El premio '{clave}' tiene un costo no numerico.") from exc
        if costo <= 0:
            raise CatalogoInvalido(f"El premio '{clave}' necesita un costo en puntos mayor que cero.")
        codigos_raw = premio.get("codigos") or []
        if not isinstance(codigos_raw, list):
            raise CatalogoInvalido(f"El premio '{clave}' tiene una lista de codigos invalida.")
        if len(codigos_raw) > MAX_CODIGOS_POR_PREMIOS:
            raise CatalogoInvalido(f"El premio '{clave}' supera el maximo de codigos permitidos.")
        codigos: list[str] = []
        for codigo_raw in codigos_raw:
            codigo = normalizar_codigo(codigo_raw)
            if codigo is None:
                raise CatalogoInvalido(
                    f"El premio '{clave}' tiene un codigo invalido: '{codigo_raw}'. "
                    "Deben ser 8 caracteres alfanumericos, con guion al medio."
                )
            if codigo in codigos_vistos:
                raise CatalogoInvalido(f"El codigo '{codigo}' esta repetido en el catalogo.")
            codigos_vistos.add(codigo)
            codigos.append(codigo)
        salida.append(
            {
                "clave": clave,
                "nombre": nombre,
                "descripcion": str(premio.get("descripcion") or "").strip(),
                "imagen": str(premio.get("imagen") or "").strip()[:500],
                "costo_puntos": costo,
                "activo": bool(premio.get("activo", True)),
                "codigos": codigos,
            }
        )
    return salida


def validar(datos: Any) -> dict:
    """Valida y normaliza un catalogo recibido."""
    if not isinstance(datos, dict):
        raise CatalogoInvalido("El catalogo debe ser un objeto JSON.")
    niveles = _validar_niveles(datos.get("niveles"))
    premios = _validar_premios(datos.get("premios"))
    try:
        version = int(datos.get("version", 1))
    except (TypeError, ValueError) as exc:
        raise CatalogoInvalido("La version del catalogo no es un numero.") from exc
    return {"version": version, "niveles": niveles, "premios": premios}


def _escribir_archivo(datos: dict) -> None:
    destino = ruta()
    destino.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        temporal = tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            delete=False,
            dir=str(destino.parent),
            prefix=".catalogo-",
            suffix=".tmp",
        )
        try:
            with temporal:
                json.dump(datos, temporal, ensure_ascii=False, indent=2)
                temporal.write("\n")
                temporal.flush()
                os.fsync(temporal.fileno())
            os.replace(temporal.name, destino)
        except BaseException:
            Path(temporal.name).unlink(missing_ok=True)
            raise
        invalidar_cache()


def _asegurar_archivo() -> Path:
    destino = ruta()
    if destino.exists():
        return destino
    datos = _catalogo_por_defecto()
    with _lock:
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_suffix(destino.suffix + ".tmp")
        if RUTA_PLANTILLA.exists():
            shutil.copyfile(RUTA_PLANTILLA, temporal)
        else:
            temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporal, destino)
        invalidar_cache()
    return destino


def leer() -> dict:
    """Lee el catalogo con cache por fecha de modificacion."""
    destino = _asegurar_archivo()
    estado = destino.stat()
    clave = str(destino)
    guardado = _cache.get(clave)
    if guardado and guardado[0] == estado.st_mtime_ns and guardado[1] == estado.st_size:
        return guardado[2]
    try:
        with destino.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)
        normalizado = validar(datos)
    except (OSError, json.JSONDecodeError, CatalogoInvalido):
        logger.exception("El catalogo en %s esta danado; se usa la plantilla por defecto.", destino)
        normalizado = validar(_catalogo_por_defecto())
    _cache[clave] = (estado.st_mtime_ns, estado.st_size, normalizado)
    return normalizado


def guardar(datos: Any, version_esperada: int | None = None) -> dict:
    """Guarda el catalogo validado. Si la version no coincide, hay conflicto."""
    actual = leer()
    version_actual = int(actual.get("version", 1))
    if version_esperada is not None and int(version_esperada) != version_actual:
        raise ConflictoCatalogo(version_actual)
    normalizado = validar(datos)
    normalizado["version"] = version_actual + 1
    _escribir_archivo(normalizado)
    return normalizado


def niveles() -> list[dict]:
    return leer()["niveles"]


def premios() -> list[dict]:
    return leer()["premios"]


def nivel_por_clave(clave: str) -> dict | None:
    objetivo = str(clave or "").strip().lower()
    return next((n for n in niveles() if n["clave"] == objetivo), None)


def premio_por_clave(clave: str) -> dict | None:
    objetivo = str(clave or "").strip().lower()
    return next((p for p in premios() if p["clave"] == objetivo), None)


def codigos_asignados(db, codigos: list[str]) -> set[str]:
    """Codigos del catalogo que ya se entregaron a algun cliente."""
    if not codigos:
        return set()
    return set(db.scalars(select(Canje.codigo).where(Canje.codigo.in_(codigos))).all())


def disponibles(db, premio: dict) -> list[str]:
    """Codigos de un premio que siguen disponibles."""
    codigos = list(premio.get("codigos") or [])
    asignados = codigos_asignados(db, codigos)
    return [codigo for codigo in codigos if codigo not in asignados]


def conteo_disponibles(db, catalogo_premios: list[dict] | None = None) -> dict[str, int]:
    """Codigos disponibles por premio (clave -> cantidad)."""
    lista = catalogo_premios if catalogo_premios is not None else premios()
    conteo: dict[str, int] = {}
    for premio in lista:
        conteo[premio["clave"]] = len(disponibles(db, premio))
    return conteo
