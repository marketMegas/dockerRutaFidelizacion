"""Respaldo opcional con un LLM compatible con la API de OpenAI.

Solo se usa cuando las reglas no reconocen la pregunta y el administrador activo
`ASISTENTE_LLM_ENABLED`. El contexto se limpia antes de salir del servidor: no
se envian cedula, telefono, email, placas ni codigos de canje.
"""

import json
import logging

import httpx

from ..config import settings
from .asistente_faq import FAQ_TEXTO

logger = logging.getLogger("fidelizacion.asistente")

SYSTEM_PROMPT = """Eres el asistente virtual del programa de fidelizacion PUNTOS G-MAX de una \
estacion de GLP. Respondes en espanol neutro, breve (maximo 120 palabras) y amable.

Reglas obligatorias:
- Usa solo la informacion del CONTEXTO. Si no esta alli, di que no tienes ese dato y sugiere \
consultar la seccion correspondiente o al personal de la estacion.
- Nunca inventes saldos, premios, fechas ni condiciones del programa.
- Nunca reveles codigos de canje ni pidas cedula, telefono, email o datos de pago.
- No prometas premios, no modifiques puntos y no ejecutes acciones; solo orientas.
- Si el usuario pide soporte humano, indica que hable con el personal de la estacion.
"""


def _configurado() -> bool:
    return bool(
        settings.ASISTENTE_LLM_ENABLED
        and settings.ASISTENTE_LLM_BASE_URL.strip()
        and settings.ASISTENTE_LLM_API_KEY.strip()
        and settings.ASISTENTE_LLM_MODEL.strip()
    )


def _contexto_limpio(contexto: dict) -> dict:
    """Reduce el contexto a datos agregados: sin identificadores ni codigos."""
    return {
        "puntos": contexto.get("puntos", 0),
        "puntos_por_litro": contexto.get("puntos_por_litro", 0),
        "nivel": contexto.get("nivel"),
        "siguiente_nivel": contexto.get("siguiente_nivel"),
        "multiplicador": contexto.get("multiplicador"),
        "consumo_mes": contexto.get("consumo_mes"),
        "consumo_mes_anterior": contexto.get("consumo_mes_anterior"),
        "faltan_para_subir": contexto.get("faltan_para_subir"),
        "faltan_para_mantener": contexto.get("faltan_para_mantener"),
        "canjes_total": contexto.get("canjes_total", 0),
        "puntos_redimidos": contexto.get("puntos_redimidos", 0),
        "canjes": [
            {
                "premio": c.get("premio"),
                "puntos_costo": c.get("puntos_costo"),
                "created_at": c.get("created_at").isoformat() if c.get("created_at") else None,
            }
            for c in contexto.get("canjes", [])
        ],
        "movimientos": [
            {
                "tipo": m.get("tipo"),
                "cantidad": m.get("cantidad"),
                "created_at": m.get("created_at").isoformat() if m.get("created_at") else None,
            }
            for m in contexto.get("movimientos", [])
        ],
        "premios": [
            {
                "nombre": p.get("nombre"),
                "descripcion": p.get("descripcion"),
                "costo_puntos": p.get("costo_puntos"),
                "codigos_disponibles": p.get("codigos_disponibles"),
                "alcanzable": p.get("alcanzable"),
                "faltan": p.get("faltan"),
            }
            for p in contexto.get("premios", [])
        ],
        "preguntas_frecuentes": FAQ_TEXTO,
    }


def consultar_llm(texto: str, historial: list[dict], contexto: dict) -> str | None:
    if not _configurado():
        return None

    base = settings.ASISTENTE_LLM_BASE_URL.rstrip("/")
    url = f"{base}/chat/completions"
    contexto_json = json.dumps(_contexto_limpio(contexto), ensure_ascii=False, indent=2)

    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in historial[-8:]:
        rol = "assistant" if item.get("rol") == "asistente" else "user"
        contenido = str(item.get("texto") or "").strip()
        if contenido:
            mensajes.append({"role": rol, "content": contenido[:500]})
    mensajes.append(
        {
            "role": "user",
            "content": f"CONTEXTO:\n{contexto_json}\n\nPREGUNTA DEL CLIENTE:\n{texto}",
        }
    )

    payload = {
        "model": settings.ASISTENTE_LLM_MODEL,
        "messages": mensajes,
        "temperature": 0.2,
        "max_tokens": settings.ASISTENTE_LLM_MAX_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {settings.ASISTENTE_LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=settings.ASISTENTE_LLM_TIMEOUT) as cliente:
            respuesta = cliente.post(url, json=payload, headers=headers)
            respuesta.raise_for_status()
            datos = respuesta.json()
        contenido = datos["choices"][0]["message"]["content"]
        return str(contenido).strip() or None
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning("El LLM del asistente no respondio: %s", exc)
        return None
