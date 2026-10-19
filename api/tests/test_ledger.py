import pytest

from app.models import Cliente, Recompensa, Venta
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


def test_acumulacion_actualiza_saldo(db):
    cliente = _cliente(db)
    venta = _venta(db, cliente, 15)
    mov = ledger.registrar_acumulacion(db, cliente, venta, 15)
    db.commit()
    assert cliente.puntos == 15
    assert mov.saldo_resultante == 15
    assert mov.tipo == "acumulacion"


def test_canje_descuenta_y_baja_stock(db):
    cliente = _cliente(db, puntos=300)
    db.add(Recompensa(nombre="Cafe", costo_puntos=100, stock=5, activa=True))
    db.commit()
    recompensa = db.query(Recompensa).first()

    canje = ledger.realizar_canje(db, cliente, recompensa)
    db.commit()
    assert cliente.puntos == 200
    assert recompensa.stock == 4
    assert canje.puntos_costo == 100


def test_canje_sin_saldo_falla(db):
    cliente = _cliente(db, puntos=10)
    db.add(Recompensa(nombre="Cafe", costo_puntos=100, stock=5, activa=True))
    db.commit()
    recompensa = db.query(Recompensa).first()

    with pytest.raises(ledger.SaldoInsuficienteError):
        ledger.realizar_canje(db, cliente, recompensa)


def test_canje_sin_stock_falla(db):
    cliente = _cliente(db, puntos=1000)
    db.add(Recompensa(nombre="Cafe", costo_puntos=100, stock=0, activa=True))
    db.commit()
    recompensa = db.query(Recompensa).first()

    with pytest.raises(ledger.LedgerError):
        ledger.realizar_canje(db, cliente, recompensa)


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
