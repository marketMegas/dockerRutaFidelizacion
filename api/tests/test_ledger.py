import pytest

from app.models import Canje, Cliente, Venta
from app.services import ledger


def _cliente(db, puntos: int = 0) -> Cliente:
    cliente = Cliente(
        cedula="10999999", placa="LED001", telefono="3000000000", nombre="Test", puntos=puntos
    )
    db.add(cliente)
    db.commit()
    return cliente


def _venta(db, cliente: Cliente, puntos: int) -> Venta:
    venta = Venta(
        cliente_id=cliente.id,
        volumen_litros=10,
        monto=1000,
        puntos_otorgados=puntos,
        id_externo=f"v-{cliente.id}-{puntos}",
    )
    db.add(venta)
    db.commit()
    return venta


def _premio(codigos=None, costo: int = 100, activo: bool = True) -> dict:
    return {
        "clave": "cafe",
        "nombre": "Cafe gratis",
        "costo_puntos": costo,
        "activo": activo,
        "codigos": list(codigos) if codigos is not None else ["AAAA-2345", "BBBB-6789", "CCCC-3456"],
    }


def test_acumulacion_actualiza_saldo(db):
    cliente = _cliente(db)
    venta = _venta(db, cliente, 15)
    mov = ledger.registrar_acumulacion(db, cliente, venta, 15)
    db.commit()
    assert cliente.puntos == 15
    assert mov.saldo_resultante == 15
    assert mov.tipo == "acumulacion"


def test_canje_descuenta_y_reserva_codigo(db):
    cliente = _cliente(db, puntos=300)
    premio = _premio()

    canje = ledger.realizar_canje(db, cliente, premio)
    db.commit()
    assert cliente.puntos == 200
    assert canje.puntos_costo == 100
    assert canje.codigo == "AAAA-2345"
    assert canje.premio_clave == "cafe"
    assert canje.premio_nombre == "Cafe gratis"


def test_canje_no_repite_codigo(db):
    cliente = _cliente(db, puntos=1000)
    premio = _premio()

    primero = ledger.realizar_canje(db, cliente, premio)
    db.commit()
    segundo = ledger.realizar_canje(db, cliente, premio)
    db.commit()

    assert primero.codigo == "AAAA-2345"
    assert segundo.codigo == "BBBB-6789"
    assert db.query(Canje).count() == 2


def test_canje_sin_saldo_falla(db):
    cliente = _cliente(db, puntos=10)
    with pytest.raises(ledger.SaldoInsuficienteError):
        ledger.realizar_canje(db, cliente, _premio())


def test_canje_sin_codigos_falla(db):
    cliente = _cliente(db, puntos=1000)
    with pytest.raises(ledger.LedgerError):
        ledger.realizar_canje(db, cliente, _premio(codigos=[]))


def test_canje_inactivo_falla(db):
    cliente = _cliente(db, puntos=1000)
    with pytest.raises(ledger.LedgerError):
        ledger.realizar_canje(db, cliente, _premio(activo=False))


def test_reverso_resta_y_no_duplica(db):
    cliente = _cliente(db)
    venta = _venta(db, cliente, 50)
    mov = ledger.registrar_acumulacion(db, cliente, venta, 50)
    db.commit()
    assert cliente.puntos == 50

    reverso = ledger.reversar_movimiento(db, mov.id, "venta anulada")
    db.commit()
    assert cliente.puntos == 0
    assert reverso.cantidad == -50

    with pytest.raises(ledger.LedgerError):
        ledger.reversar_movimiento(db, mov.id, "otra vez")


def test_reverso_de_canje_devuelve_el_codigo_al_pool(db):
    cliente = _cliente(db, puntos=1000)
    premio = _premio()
    canje = ledger.realizar_canje(db, cliente, premio)
    db.commit()
    assert canje.codigo == "AAAA-2345"

    mov = db.query(ledger.LedgerPuntos).filter(ledger.LedgerPuntos.referencia == f"canje:{canje.id}").one()
    ledger.reversar_movimiento(db, mov.id, "canje anulado")
    db.commit()

    assert cliente.puntos == 1000
    assert db.query(Canje).count() == 0
    # El codigo vuelve a estar disponible para el siguiente canje.
    siguiente = ledger.realizar_canje(db, cliente, premio)
    db.commit()
    assert siguiente.codigo == "AAAA-2345"
