"""Importa codigos existentes desde un Excel, agrupados por puntos asignados."""

import argparse
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

from app.services import catalogo

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
HOJA = "xl/worksheets/sheet1.xml"
CADENAS = "xl/sharedStrings.xml"


def _sin_acentos(valor: str) -> str:
    normalizado = unicodedata.normalize("NFD", valor)
    return "".join(ch for ch in normalizado if unicodedata.category(ch) != "Mn")


def _texto(valor: str | None) -> str:
    return str(valor or "").strip()


def _entero(valor: str, campo: str) -> int:
    limpio = _texto(valor).replace(".", "").replace(",", "")
    try:
        return int(float(limpio))
    except ValueError as exc:
        raise SystemExit(f"Valor invalido en '{campo}': {valor!r}") from exc


def _columna(ref: str) -> str:
    return "".join(ch for ch in ref if ch.isalpha())


def _leer_filas(ruta: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(ruta) as libro:
        cadenas: list[str] = []
        if CADENAS in libro.namelist():
            raiz = ET.fromstring(libro.read(CADENAS))
            for item in raiz.findall(f"{NS}si"):
                cadenas.append("".join(t.text or "" for t in item.iter(f"{NS}t")))
        hoja = ET.fromstring(libro.read(HOJA))

    filas: list[dict[str, str]] = []
    for fila in hoja.iter(f"{NS}row"):
        datos: dict[str, str] = {}
        for celda in fila.findall(f"{NS}c"):
            valor = celda.find(f"{NS}v")
            if valor is None:
                inline = celda.find(f"{NS}is")
                texto = "".join(t.text or "" for t in inline.iter(f"{NS}t")) if inline is not None else ""
            elif celda.get("t") == "s":
                texto = cadenas[int(valor.text or 0)]
            else:
                texto = valor.text or ""
            datos[_columna(celda.get("r", ""))] = texto
        filas.append(datos)
    return filas


def _indice_columnas(encabezado: dict[str, str]) -> dict[str, str]:
    columnas = {_sin_acentos(valor).strip().lower(): clave for clave, valor in encabezado.items()}
    requeridas = ("puntos asignados", "codigo")
    for nombre in requeridas:
        if nombre not in columnas:
            raise SystemExit(f"Falta la columna '{nombre}' en el Excel.")
    return columnas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xlsx", type=Path, help="Ruta del archivo Excel")
    parser.add_argument("--clave-prefijo", default="bono", help="Prefijo de la clave de cada premio")
    args = parser.parse_args()

    if not args.xlsx.exists():
        raise SystemExit(f"No existe el archivo: {args.xlsx}")

    filas = _leer_filas(args.xlsx)
    if not filas:
        raise SystemExit("El Excel no tiene filas.")
    columnas = _indice_columnas(filas[0])
    col_puntos = columnas["puntos asignados"]
    col_codigo = columnas["codigo"]
    col_valor = columnas.get("valor del bono")

    grupos: dict[int, list[str]] = defaultdict(list)
    vistos: set[str] = set()
    for numero, fila in enumerate(filas[1:], start=2):
        puntos = _entero(fila.get(col_puntos, ""), f"puntos (fila {numero})")
        if puntos <= 0:
            raise SystemExit(f"Puntos invalidos en la fila {numero}: {puntos}")
        codigo = catalogo.normalizar_codigo(fila.get(col_codigo, ""))
        if codigo is None:
            raise SystemExit(f"Codigo invalido en la fila {numero}: {fila.get(col_codigo)!r}")
        if codigo in vistos:
            raise SystemExit(f"Codigo repetido en la fila {numero}: {codigo}")
        vistos.add(codigo)
        if col_valor:
            valor = _entero(fila.get(col_valor, ""), f"valor (fila {numero})")
            if valor != puntos * 1000:
                raise SystemExit(
                    f"El valor de la fila {numero} no coincide con los puntos: {valor} != {puntos * 1000}"
                )
        grupos[puntos].append(codigo)

    premios = []
    for puntos in sorted(grupos):
        valor = puntos * 1000
        nombre = f"Bono ${valor:,.0f}".replace(",", ".")
        premios.append(
            {
                "clave": f"{args.clave_prefijo}-{puntos}",
                "nombre": nombre,
                "descripcion": f"Codigo de bono por {nombre} para redimir en las marcas aliadas.",
                "imagen": "",
                "costo_puntos": puntos,
                "activo": True,
                "codigos": grupos[puntos],
            }
        )

    actual = catalogo.leer()
    datos = {"version": actual["version"], "niveles": actual["niveles"], "premios": premios}
    guardado = catalogo.guardar(datos, version_esperada=actual["version"])

    print(f"Archivo: {args.xlsx}")
    print(f"Codigos importados: {len(vistos)}")
    print(f"Premios: {len(premios)}")
    for premio in guardado["premios"]:
        print(
            f"  {premio['clave']}: {premio['nombre']} - "
            f"{premio['costo_puntos']} pts - {len(premio['codigos'])} codigos"
        )
    print(f"Version del catalogo: {guardado['version']}")


if __name__ == "__main__":
    main()
