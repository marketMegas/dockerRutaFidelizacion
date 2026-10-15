import csv
import json
import os
from pathlib import Path

import requests

CAMPOS = {
    "id_externo": ["id_factura", "id_externo", "id", "factura", "numero"],
    "volumen_litros": ["volumen_lt", "volumen", "litros", "galones", "cantidad"],
    "monto": ["valor_total", "total", "monto", "valor"],
    "placa": ["placa", "vehiculo", "patente"],
    "telefono": ["telefono", "celular", "movil"],
    "qr_payload": ["qr", "qr_payload", "codigo_qr"],
    "fecha_hora": ["fecha_hora", "fecha", "fechaHora"],
}


def _buscar(fila, campo):
    for nombre in CAMPOS[campo]:
        for clave in fila:
            if clave and clave.strip().lower() == nombre.lower():
                valor = fila[clave]
                return valor.strip() if isinstance(valor, str) else valor
    return None


def normalizar(fila, estacion_id):
    venta = {"estacion_id": estacion_id}
    for campo in CAMPOS:
        valor = _buscar(fila, campo)
        if valor not in (None, ""):
            venta[campo] = valor
    if "id_externo" in venta:
        venta["id_externo"] = str(venta["id_externo"])
    if "volumen_litros" in venta:
        venta["volumen_litros"] = float(str(venta["volumen_litros"]).replace(",", "."))
    if "monto" in venta:
        venta["monto"] = float(str(venta["monto"]).replace(",", "."))
    return venta


def desde_api(url, api_key, estacion_id):
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, dict):
        data = data.get("ventas") or data.get("data") or data.get("items") or []
    return [normalizar(f, estacion_id) for f in data]


def _archivo_procesados(archivo):
    return Path(str(archivo) + ".procesados.json")


def desde_archivo(archivo, estacion_id):
    path = Path(archivo)
    if not path.exists():
        return []
    marcador = _archivo_procesados(archivo)
    vistos = set(json.loads(marcador.read_text(encoding="utf-8"))) if marcador.exists() else set()

    with path.open(encoding="utf-8-sig", newline="") as fh:
        muestra = fh.read(4096)
        fh.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t|")
        except csv.Error:
            dialecto = csv.excel
        filas = list(csv.DictReader(fh, dialect=dialecto))

    nuevas = []
    for fila in filas:
        venta = normalizar(fila, estacion_id)
        id_ext = venta.get("id_externo")
        if not id_ext or id_ext in vistos:
            continue
        vistos.add(id_ext)
        nuevas.append(venta)

    marcador.write_text(json.dumps(sorted(vistos), ensure_ascii=False), encoding="utf-8")
    return nuevas


def obtener(modo, estacion_id):
    if modo == "api":
        return desde_api(os.getenv("ZENCILLO_API_URL", ""), os.getenv("ZENCILLO_API_KEY", ""), estacion_id)
    if modo == "archivos":
        return desde_archivo(os.getenv("ZENCILLO_ARCHIVO", "ventas_zencillo.csv"), estacion_id)
    return []
