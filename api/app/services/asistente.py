"""Asistente virtual del cliente: contexto de sesion y respuestas deterministas.

Las reglas se responden siempre en el backend con datos reales del cliente.
El LLM es un respaldo opcional solo para preguntas que las reglas no cubren; el
contexto que se le envia no contiene cedula, telefono, email, placas ni codigos.
"""

import unicodedata

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Canje, Cliente, LedgerPuntos
from . import catalogo, niveles
from .asistente_llm import consultar_llm
from .motor_de_reglas import regla_vigente

ACCIONES = {
    "recompensas": {"tipo": "navegar", "vista": "recompensas", "label": "Ver recompensas"},
    "historial": {"tipo": "navegar", "vista": "historial", "label": "Ver historial"},
    "ayuda": {"tipo": "navegar", "vista": "ayuda", "label": "Ver ayuda"},
    "inicio": {"tipo": "navegar", "vista": "inicio", "label": "Ir al inicio"},
}

SUGERENCIAS = [
    "¿Cuántos puntos tengo?",
    "¿Qué premios puedo canjear?",
    "¿Cuánto me falta para subir de nivel?",
    "¿Qué he canjeado?",
]

NO_CODIGOS = "Por seguridad no muestro códigos en el chat. Entra a Recompensas > Mis códigos para verlos y copiarlos."


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).strip()


def _numero(valor: float) -> str:
    return f"{float(valor):.1f}".rstrip("0").rstrip(".")


def _fecha(valor) -> str:
    if valor is None:
        return "-"
    return valor.strftime("%d/%m/%Y %H:%M")


def _nivel_actual(contexto: dict) -> dict | None:
    return contexto.get("nivel")


def _menciona_premio(texto: str, premio: dict) -> bool:
    nombre = _normalizar(premio["nombre"])
    if nombre in texto or premio["clave"] in texto:
        return True
    return any(len(palabra) >= 4 and palabra in texto for palabra in nombre.split())


def construir_contexto(db: Session, cliente: Cliente) -> dict:
    """Reune los datos de la sesion sin incluir identificadores personales ni codigos."""
    nivel = niveles.nivel_efectivo(db, cliente.id)
    regla = regla_vigente(db)

    total_canjes, total_redimido = db.execute(
        select(func.count(Canje.id), func.coalesce(func.sum(Canje.puntos_costo), 0)).where(
            Canje.cliente_id == cliente.id
        )
    ).one()

    canjes = db.scalars(
        select(Canje).where(Canje.cliente_id == cliente.id).order_by(Canje.id.desc()).limit(20)
    ).all()
    movimientos = db.scalars(
        select(LedgerPuntos)
        .where(LedgerPuntos.cliente_id == cliente.id)
        .order_by(LedgerPuntos.id.desc())
        .limit(10)
    ).all()

    premios = [p for p in catalogo.premios() if p["activo"]]
    disponibles = catalogo.conteo_disponibles(db, premios)

    return {
        "puntos": int(cliente.puntos),
        "puntos_por_litro": float(regla.puntos_por_litro) if regla is not None else 0.0,
        "nivel": nivel["nivel"],
        "siguiente_nivel": nivel["siguiente"],
        "multiplicador": nivel["multiplicador"],
        "consumo_mes": nivel["litros_mes"],
        "consumo_mes_anterior": nivel["litros_mes_anterior"],
        "faltan_para_subir": nivel["faltan_para_subir"],
        "faltan_para_mantener": nivel["faltan_para_mantener"],
        "canjes_total": int(total_canjes or 0),
        "puntos_redimidos": int(total_redimido or 0),
        "canjes": [
            {
                "premio": c.premio_nombre,
                "premio_clave": c.premio_clave,
                "puntos_costo": int(c.puntos_costo),
                "created_at": c.created_at,
            }
            for c in canjes
        ],
        "movimientos": [
            {
                "tipo": m.tipo,
                "cantidad": int(m.cantidad),
                "saldo_resultante": int(m.saldo_resultante),
                "motivo": m.motivo or m.referencia or "",
                "created_at": m.created_at,
            }
            for m in movimientos
        ],
        "premios": [
            {
                "clave": p["clave"],
                "nombre": p["nombre"],
                "descripcion": p["descripcion"],
                "costo_puntos": int(p["costo_puntos"]),
                "codigos_disponibles": int(disponibles.get(p["clave"], 0)),
                "alcanzable": int(cliente.puntos) >= int(p["costo_puntos"]),
                "faltan": max(0, int(p["costo_puntos"]) - int(cliente.puntos)),
            }
            for p in sorted(premios, key=lambda p: int(p["costo_puntos"]))
        ],
    }


def detectar_intent(texto: str, contexto: dict) -> str:
    t = _normalizar(texto)
    if not t or t in {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}:
        return "ayuda"
    if any(p in t for p in ("como estas", "que puedes hacer", "ayuda", "como funciona", "instrucciones")):
        return "ayuda"

    if any(p in t for p in ("codigo", "codigos", "donde veo", "donde esta mi codigo")):
        return "donde_codigo"

    if any(p in t for p in ("he canjeado", "canjeados", "mis canjes", "lista de canjes", "historial de canjes")):
        return "lista_canjes"
    if any(p in t for p in ("redim", "gastad", "puntos usados")):
        return "redimidos_total"
    if any(p in t for p in ("como canje", "como canjear", "como canjeo", "donde canjeo")):
        return "como_canjear"

    if any(_menciona_premio(t, p) for p in contexto["premios"]):
        return "premio_especifico"

    if any(p in t for p in ("recompensa", "premio", "puedo canjear", "disponibles", "catalogo")):
        return "premios"

    if "nivel" in t or "multiplicador" in t or "litro" in t or "subir de nivel" in t:
        return "nivel"

    if any(p in t for p in ("movimiento", "historial", "puntos ganados", "ventas", "ganado")):
        return "movimientos"

    if any(p in t for p in ("saldo", "cuanto", "cuantos", "puntos tengo", "puntos disponibles")):
        if "punto" in t or "saldo" in t:
            return "saldo"

    return "desconocido"


def _respuesta_ayuda() -> dict:
    return {
        "respuesta": (
            "Puedo ayudarte con tus puntos, nivel, canjes, recompensas y movimientos. "
            "Prueba con una sugerencia o escribe tu pregunta."
        ),
        "intent": "ayuda",
        "acciones": [ACCIONES["recompensas"], ACCIONES["historial"], ACCIONES["ayuda"]],
        "datos": {},
    }


def _respuesta_saldo(contexto: dict) -> dict:
    nivel = _nivel_actual(contexto)
    extra = f" Estás en nivel **{nivel['nombre']}**." if nivel else ""
    return {
        "respuesta": f"Tienes **{contexto['puntos']} puntos** disponibles.{extra}",
        "intent": "saldo",
        "acciones": [ACCIONES["recompensas"]],
        "datos": {"puntos": contexto["puntos"]},
    }


def _respuesta_nivel(contexto: dict) -> dict:
    nivel = _nivel_actual(contexto)
    if not nivel:
        return {
            "respuesta": "No tengo información de tu nivel en este momento.",
            "intent": "nivel",
            "acciones": [ACCIONES["inicio"]],
            "datos": {},
        }

    lineas = [
        f"Tu nivel actual es **{nivel['nombre']}** (multiplicador x{_numero(nivel['multiplicador'])}).",
        f"Consumo de este mes: **{_numero(contexto['consumo_mes'])} L** "
        f"(mes anterior: {_numero(contexto['consumo_mes_anterior'])} L).",
    ]
    siguiente = contexto.get("siguiente_nivel")
    if siguiente:
        lineas.append(
            f"Te faltan **{_numero(contexto['faltan_para_subir'])} L** para subir a **{siguiente['nombre']}**."
        )
    else:
        lineas.append("Ya estás en el nivel más alto del programa.")

    if contexto.get("faltan_para_mantener", 0) > 0:
        lineas.append(
            f"Para mantener **{nivel['nombre']}** este mes te faltan "
            f"**{_numero(contexto['faltan_para_mantener'])} L**."
        )

    return {
        "respuesta": "\n".join(lineas),
        "intent": "nivel",
        "acciones": [ACCIONES["inicio"]],
        "datos": {
            "nivel": nivel["clave"],
            "multiplicador": nivel["multiplicador"],
            "siguiente_nivel": siguiente["clave"] if siguiente else None,
        },
    }


def _respuesta_canjes_resumen(contexto: dict) -> dict:
    total = contexto["canjes_total"]
    if total == 0:
        return {
            "respuesta": (
                "Aún no has redimido ningún premio. Tienes "
                f"**{contexto['puntos']} puntos** disponibles."
            ),
            "intent": "redimidos_total",
            "acciones": [ACCIONES["recompensas"]],
            "datos": {"canjes_total": 0, "puntos_redimidos": 0},
        }

    ultimo = contexto["canjes"][0]
    return {
        "respuesta": (
            f"Has canjeado **{total} premio{'s' if total != 1 else ''}** y usado "
            f"**{contexto['puntos_redimidos']} puntos**.\n"
            f"Tu último canje fue **{ultimo['premio']}** el {_fecha(ultimo['created_at'])}."
        ),
        "intent": "redimidos_total",
        "acciones": [ACCIONES["recompensas"]],
        "datos": {
            "canjes_total": total,
            "puntos_redimidos": contexto["puntos_redimidos"],
        },
    }


def _respuesta_lista_canjes(contexto: dict) -> dict:
    canjes = contexto["canjes"]
    if not canjes:
        return {
            "respuesta": (
                "Aún no has canjeado premios. Puedes ver las recompensas disponibles en la sección Recompensas."
            ),
            "intent": "lista_canjes",
            "acciones": [ACCIONES["recompensas"]],
            "datos": {"canjes": []},
        }

    lineas = [
        f"- **{c['premio']}** · {c['puntos_costo']} pts · {_fecha(c['created_at'])}"
        for c in canjes[:10]
    ]
    if len(canjes) > 10:
        lineas.append(f"... y {len(canjes) - 10} canjes más.")
    return {
        "respuesta": "Tus últimos canjes:\n" + "\n".join(lineas) + "\n\n" + NO_CODIGOS,
        "intent": "lista_canjes",
        "acciones": [ACCIONES["recompensas"]],
        "datos": {
            "canjes": [
                {
                    "premio": c["premio"],
                    "puntos_costo": c["puntos_costo"],
                    "created_at": c["created_at"],
                }
                for c in canjes[:10]
            ]
        },
    }


def _respuesta_premios(contexto: dict) -> dict:
    premios = contexto["premios"]
    if not premios:
        return {
            "respuesta": "No hay recompensas activas en este momento.",
            "intent": "premios",
            "acciones": [ACCIONES["recompensas"]],
            "datos": {"premios": []},
        }

    lineas = []
    for p in premios[:8]:
        estado = "disponible" if p["codigos_disponibles"] > 0 else "sin códigos"
        if p["alcanzable"]:
            lineas.append(
                f"- **{p['nombre']}** · {p['costo_puntos']} pts · puedes canjearlo · {estado}"
            )
        else:
            lineas.append(
                f"- **{p['nombre']}** · {p['costo_puntos']} pts · te faltan {p['faltan']} pts · {estado}"
            )
    return {
        "respuesta": (
            f"Tienes **{contexto['puntos']} puntos** disponibles.\n\n"
            "Recompensas disponibles:\n" + "\n".join(lineas)
        ),
        "intent": "premios",
        "acciones": [ACCIONES["recompensas"]],
        "datos": {"puntos": contexto["puntos"], "premios": premios[:8]},
    }


def _respuesta_premio_especifico(texto: str, contexto: dict) -> dict:
    t = _normalizar(texto)
    premio = None
    for p in contexto["premios"]:
        if _menciona_premio(t, p):
            premio = p
            break

    if premio is None:
        return _respuesta_premios(contexto)

    if premio["codigos_disponibles"] <= 0:
        estado = "Ahora mismo no hay códigos disponibles para este premio."
    elif premio["alcanzable"]:
        estado = "Puedes canjearlo ahora mismo desde Recompensas."
    else:
        estado = f"Te faltan **{premio['faltan']} puntos** para canjearlo."

    return {
        "respuesta": (
            f"**{premio['nombre']}** cuesta **{premio['costo_puntos']} puntos**. "
            f"Tienes **{contexto['puntos']}**. {estado}"
        ),
        "intent": "premio_especifico",
        "acciones": [ACCIONES["recompensas"]],
        "datos": {"premio": premio},
    }


def _respuesta_movimientos(contexto: dict) -> dict:
    movimientos = contexto["movimientos"]
    if not movimientos:
        return {
            "respuesta": "Todavía no tienes movimientos registrados.",
            "intent": "movimientos",
            "acciones": [ACCIONES["historial"]],
            "datos": {"movimientos": []},
        }

    etiquetas = {
        "acumulacion": "Puntos ganados",
        "canje": "Canje",
        "reverso": "Ajuste",
        "ajuste": "Ajuste",
    }
    lineas = []
    for m in movimientos:
        signo = "+" if m["cantidad"] > 0 else ""
        lineas.append(
            f"- {etiquetas.get(m['tipo'], m['tipo'])}: {signo}{m['cantidad']} pts "
            f"(saldo {m['saldo_resultante']}) · {_fecha(m['created_at'])}"
        )
    return {
        "respuesta": "Tus últimos movimientos:\n" + "\n".join(lineas),
        "intent": "movimientos",
        "acciones": [ACCIONES["historial"]],
        "datos": {
            "movimientos": [
                {
                    "tipo": m["tipo"],
                    "cantidad": m["cantidad"],
                    "created_at": m["created_at"],
                }
                for m in movimientos
            ]
        },
    }


def _respuesta_donde_codigo() -> dict:
    return {
        "respuesta": NO_CODIGOS,
        "intent": "donde_codigo",
        "acciones": [ACCIONES["recompensas"]],
        "datos": {},
    }


def _respuesta_como_canjear() -> dict:
    return {
        "respuesta": (
            "En **Recompensas** elige un premio que alcance con tus puntos y toca **Canjear**. "
            "Recibirás un código al instante; queda guardado en **Mis códigos** para que lo "
            "muestres en los comercios aliados."
        ),
        "intent": "como_canjear",
        "acciones": [ACCIONES["recompensas"]],
        "datos": {},
    }


def _respuesta_desconocida() -> dict:
    return {
        "respuesta": (
            "No entendí tu pregunta. Puedo ayudarte con puntos, nivel, canjes, recompensas y "
            "movimientos. Prueba con una de las sugerencias."
        ),
        "intent": "desconocido",
        "acciones": [ACCIONES["recompensas"], ACCIONES["historial"], ACCIONES["ayuda"]],
        "datos": {},
    }


def responder_reglas(texto: str, contexto: dict) -> dict:
    intent = detectar_intent(texto, contexto)
    if intent == "ayuda":
        resultado = _respuesta_ayuda()
    elif intent == "saldo":
        resultado = _respuesta_saldo(contexto)
    elif intent == "nivel":
        resultado = _respuesta_nivel(contexto)
    elif intent == "redimidos_total":
        resultado = _respuesta_canjes_resumen(contexto)
    elif intent == "lista_canjes":
        resultado = _respuesta_lista_canjes(contexto)
    elif intent == "premios":
        resultado = _respuesta_premios(contexto)
    elif intent == "premio_especifico":
        resultado = _respuesta_premio_especifico(texto, contexto)
    elif intent == "movimientos":
        resultado = _respuesta_movimientos(contexto)
    elif intent == "donde_codigo":
        resultado = _respuesta_donde_codigo()
    elif intent == "como_canjear":
        resultado = _respuesta_como_canjear()
    else:
        resultado = _respuesta_desconocida()
    resultado["fuente"] = "reglas"
    return resultado


def responder(db: Session, cliente: Cliente, texto: str, historial: list[dict]) -> dict:
    contexto = construir_contexto(db, cliente)
    resultado = responder_reglas(texto, contexto)

    if resultado["intent"] == "desconocido" and settings.ASISTENTE_LLM_ENABLED:
        respuesta_llm = consultar_llm(texto, historial, contexto)
        if respuesta_llm:
            resultado = {
                "respuesta": respuesta_llm,
                "intent": "llm",
                "fuente": "llm",
                "acciones": [ACCIONES["recompensas"], ACCIONES["historial"], ACCIONES["ayuda"]],
                "datos": {},
            }

    return resultado
