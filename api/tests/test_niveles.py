from datetime import timedelta

from app.models import Cliente, Venta
from app.services import niveles, periodo

ESCALA = [
    {"clave": "arranque", "nombre": "Arranque", "minimo": 1, "multiplicador": 1.0},
    {"clave": "plata", "nombre": "Plata", "minimo": 100, "multiplicador": 1.25},
    {"clave": "oro", "nombre": "Oro", "minimo": 250, "multiplicador": 1.5},
    {"clave": "diamante", "nombre": "Diamante", "minimo": 500, "multiplicador": 2.0},
]

_ventas = 0


def _cliente(db) -> Cliente:
    cliente = Cliente(cedula="10999999", placa="NIV001", telefono="3000000001", nombre="Niveles")
    db.add(cliente)
    db.commit()
    return cliente


def _venta(db, cliente: Cliente, litros: float, created_at=None) -> Venta:
    global _ventas
    _ventas += 1
    venta = Venta(
        cliente_id=cliente.id,
        volumen_litros=litros,
        monto=litros * 100,
        puntos_otorgados=int(litros),
        id_externo=f"n-{cliente.id}-{_ventas}",
        created_at=created_at or periodo.ahora_utc(),
    )
    db.add(venta)
    db.commit()
    return venta


def _venta_mes_anterior(db, cliente: Cliente, litros: float) -> Venta:
    """Venta fechada dentro del mes anterior al actual."""
    return _venta(db, cliente, litros, periodo.inicio_mes_anterior_utc() + timedelta(days=1))


def test_nivel_por_litros():
    assert niveles.nivel_por_litros(0, ESCALA)["nivel"]["clave"] == "arranque"
    assert niveles.nivel_por_litros(1, ESCALA)["nivel"]["clave"] == "arranque"
    assert niveles.nivel_por_litros(99, ESCALA)["nivel"]["clave"] == "arranque"
    assert niveles.nivel_por_litros(99.9, ESCALA)["nivel"]["clave"] == "arranque"
    assert niveles.nivel_por_litros(100, ESCALA)["nivel"]["clave"] == "plata"
    assert niveles.nivel_por_litros(249.9, ESCALA)["nivel"]["clave"] == "plata"
    assert niveles.nivel_por_litros(250, ESCALA)["nivel"]["clave"] == "oro"
    assert niveles.nivel_por_litros(499.9, ESCALA)["nivel"]["clave"] == "oro"
    assert niveles.nivel_por_litros(500, ESCALA)["nivel"]["clave"] == "diamante"
    assert niveles.nivel_por_litros(900, ESCALA)["nivel"]["clave"] == "diamante"


def test_siguiente_nivel():
    assert niveles.nivel_por_litros(0, ESCALA)["siguiente"]["clave"] == "plata"
    assert niveles.nivel_por_litros(99, ESCALA)["siguiente"]["clave"] == "plata"
    assert niveles.nivel_por_litros(100, ESCALA)["siguiente"]["clave"] == "oro"
    assert niveles.nivel_por_litros(250, ESCALA)["siguiente"]["clave"] == "diamante"
    assert niveles.nivel_por_litros(500, ESCALA)["siguiente"] is None


def test_el_mes_anterior_manda():
    # Mes anterior 500 L (Diamante) y mes actual 0 L: el nivel se conserva.
    info = niveles.calcular_nivel(500, 0, ESCALA)
    assert info["nivel"]["clave"] == "diamante"
    assert info["multiplicador"] == 2.0
    assert info["faltan_para_mantener"] == 500


def test_el_mes_actual_manda():
    info = niveles.calcular_nivel(0, 500, ESCALA)
    assert info["nivel"]["clave"] == "diamante"
    assert info["multiplicador"] == 2.0


def test_faltan_para_mantener_y_subir():
    # Venia de Plata (120 L el mes pasado) y este mes va en 10 L.
    info = niveles.calcular_nivel(120, 10, ESCALA)
    assert info["nivel"]["clave"] == "plata"
    assert info["faltan_para_mantener"] == 90
    assert info["faltan_para_subir"] == 240


def test_baja_de_nivel_al_terminar_el_mes():
    # Mes anterior 120 L (Plata) y este mes 10 L: en el mes que viene seria Arranque.
    info = niveles.calcular_nivel(120, 10, ESCALA)
    assert info["nivel"]["clave"] == "plata"
    assert niveles.calcular_nivel(10, 0, ESCALA)["nivel"]["clave"] == "arranque"


def test_nivel_efectivo_desde_la_base(db):
    cliente = _cliente(db)
    _venta_mes_anterior(db, cliente, 120)
    info = niveles.nivel_efectivo(db, cliente.id)
    assert info["nivel"]["clave"] == "plata"
    assert info["litros_mes_anterior"] == 120
    assert info["litros_mes"] == 0


def test_nivel_efectivo_suma_litros_extra(db):
    cliente = _cliente(db)
    info = niveles.nivel_efectivo(db, cliente.id, litros_extra=100)
    assert info["nivel"]["clave"] == "plata"
    assert info["litros_mes"] == 100


def test_consumo_del_mes_usa_el_corte_local(db):
    cliente = _cliente(db)
    _venta(db, cliente, 50)
    consumos = niveles.consumos_por_cliente(db, periodo.inicio_mes_utc())
    assert consumos.get(cliente.id) == 50
