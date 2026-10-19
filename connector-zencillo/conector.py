import argparse
import os
import sys
import time

import requests
from dotenv import load_dotenv

import cola
import fuentes

load_dotenv()

API_URL = os.getenv("FID_API_URL", "http://localhost:8002/fid-api").rstrip("/")
API_KEY = os.getenv("SYNC_API_KEY", "dev-api-key")
ESTACION = os.getenv("ESTACION_ID", "EDS-01")
MODO = os.getenv("ZENCILLO_MODO", "simulador")
POLL = int(os.getenv("POLL_SEGUNDOS", "30"))


def enviar(venta):
    try:
        resp = requests.post(
            f"{API_URL}/sync/venta",
            json=venta,
            headers={"X-API-Key": API_KEY},
            timeout=10,
        )
    except requests.RequestException as exc:
        return False, {"error": f"sin conexion: {exc}"}

    if resp.status_code == 200:
        return True, resp.json()
    try:
        detalle = resp.json()
    except ValueError:
        detalle = resp.text[:200]
    return False, {"error": f"HTTP {resp.status_code}: {detalle}"}


def registrar(venta):
    ok, resp = enviar(venta)
    if ok:
        cola.quitar(venta["id_externo"])
        return {"estado": "ok", **resp}
    creada = cola.encolar(venta)
    return {"estado": "pendiente" if creada else "ya_en_cola", **resp}


def sincronizar():
    items = cola.cargar()
    enviados = 0
    for venta in items:
        ok, _ = enviar(venta)
        if ok:
            cola.quitar(venta["id_externo"])
            enviados += 1
    return enviados, len(items) - enviados


def venta_simulada(args):
    id_externo = args.factura or f"SIM-{int(time.time() * 1000)}"
    venta = {
        "id_externo": str(id_externo),
        "estacion_id": ESTACION,
        "volumen_litros": args.litros,
        "monto": args.monto if args.monto is not None else round(args.litros * 3200, 2),
        "placa": args.placa,
    }
    if args.telefono:
        venta["telefono"] = args.telefono
    return venta


def cmd_simular(args):
    resp = registrar(venta_simulada(args))
    print(resp)


def cmd_sincronizar(_args):
    enviados, pendientes = sincronizar()
    print({"enviados": enviados, "pendientes": pendientes})


def cmd_cola(_args):
    itemspend = cola.pendientes()
    print(f"Pendientes: {len(itemspend)}")
    for v in itemspend:
        print(f"  - {v.get('id_externo')} | {v.get('volumen_litros')} L | {v.get('placa')}")


def cmd_daemon(_args):
    print(f"Conector en modo '{MODO}' -> {API_URL} (cada {POLL}s). Ctrl+C para salir.")
    while True:
        try:
            ventas = fuentes.obtener(MODO, ESTACION)
        except Exception as exc:
            ventas = []
            print(f"[origen] error: {exc}")
        for venta in ventas:
            print(venta.get("id_externo"), "->", registrar(venta))
        if cola.pendientes():
            sincronizar()
        time.sleep(POLL)


def menu():
    while True:
        print("\n=== Conector Fidelizacion GLP ===")
        print(f"API: {API_URL} | modo: {MODO} | estacion: {ESTACION}")
        print("1) Registrar venta simulada")
        print("2) Ver cola pendiente")
        print("3) Sincronizar cola")
        print("4) Salir")
        opcion = input("Opcion: ").strip()

        if opcion == "1":
            litros = float(input("Litros: ").strip())
            placa = input("Placa: ").strip() or "SINPLACA"
            telefono = input("Telefono del cliente (opcional): ").strip()
            args = argparse.Namespace(
                litros=litros, placa=placa, telefono=telefono or None,
                factura=None, monto=None,
            )
            print(registrar(venta_simulada(args)))
        elif opcion == "2":
            cmd_cola(None)
        elif opcion == "3":
            cmd_sincronizar(None)
        elif opcion == "4":
            break
        else:
            print("Opcion no valida")


def main():
    parser = argparse.ArgumentParser(description="Conector de fidelizacion para estaciones GLP")
    sub = parser.add_subparsers(dest="comando")

    p_sim = sub.add_parser("simular", help="Registra una venta manual")
    p_sim.add_argument("--litros", type=float, required=True)
    p_sim.add_argument("--placa", default="SINPLACA")
    p_sim.add_argument("--telefono")
    p_sim.add_argument("--factura")
    p_sim.add_argument("--monto", type=float)
    p_sim.set_defaults(func=cmd_simular)

    sub.add_parser("sincronizar", help="Reintenta la cola offline").set_defaults(func=cmd_sincronizar)
    sub.add_parser("cola", help="Muestra ventas pendientes").set_defaults(func=cmd_cola)
    sub.add_parser("daemon", help="Consulta el origen de Zencillo periodicamente").set_defaults(func=cmd_daemon)

    args = parser.parse_args()
    if not args.comando:
        menu()
        return
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
