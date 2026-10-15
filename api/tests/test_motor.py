from datetime import timedelta
from decimal import Decimal

from app.models import Regla, utcnow
from app.services.motor_de_reglas import calcular_puntos, regla_vigente


def test_sin_reglas_no_otorga_puntos(db):
    puntos, regla = calcular_puntos(db, 10)
    assert puntos == 0
    assert regla is None


def test_regla_base_redondea_hacia_abajo(db):
    db.add(Regla(nombre="Base", puntos_por_litro=Decimal("1.50")))
    db.commit()
    puntos, regla = calcular_puntos(db, 10.4)
    assert puntos == 15
    assert regla.nombre == "Base"


def test_regla_inactiva_se_ignora(db):
    db.add(Regla(nombre="Inactiva", puntos_por_litro=Decimal("5.00"), activa=False))
    db.commit()
    puntos, regla = calcular_puntos(db, 10)
    assert puntos == 0
    assert regla is None


def test_prioridad_manda(db):
    db.add(Regla(nombre="Baja", puntos_por_litro=Decimal("1.00"), prioridad=1))
    db.add(Regla(nombre="Alta", puntos_por_litro=Decimal("2.00"), prioridad=10))
    db.commit()
    puntos, regla = calcular_puntos(db, 10)
    assert regla.nombre == "Alta"
    assert puntos == 20


def test_vigencia_por_fechas(db):
    ahora = utcnow()
    db.add(Regla(nombre="Vencida", puntos_por_litro=Decimal("9.00"), prioridad=5, hasta=ahora - timedelta(days=1)))
    db.add(Regla(nombre="Futura", puntos_por_litro=Decimal("9.00"), prioridad=5, desde=ahora + timedelta(days=1)))
    db.commit()
    assert regla_vigente(db, ahora) is None

    db.add(Regla(nombre="Hoy", puntos_por_litro=Decimal("0.50"), prioridad=1, desde=ahora - timedelta(days=1)))
    db.commit()
    puntos, regla = calcular_puntos(db, 20, ahora)
    assert regla.nombre == "Hoy"
    assert puntos == 10
