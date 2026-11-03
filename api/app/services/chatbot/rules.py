# -*- coding: utf-8 -*-
import re
import unicodedata
from difflib import get_close_matches


def normalizar(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.lower().strip()
    # quitar tildes
    texto = ''.join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))
    # quitar puntuacion simple
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto


INTENCIONES = [
    {
        "clave": "SALUDO",
        "keywords": ["hola", "buenos", "buenas", "hey", "hi", "saludos"],
        "sugerencias": ["Mis puntos", "Mi nivel", "Catálogo de premios", "Mis códigos"]
    },
    {
        "clave": "SALDO_PUNTOS",
        "keywords": ["punto", "puntos", "saldo", "cuantos", "tengo"],
        "sugerencias": ["Mi nivel", "Catálogo de premios", "Mis códigos"]
    },
    {
        "clave": "NIVEL",
        "keywords": ["nivel", "multiplicador", "rango"],
        "sugerencias": ["Cómo gano puntos", "Mis puntos", "Catálogo de premios"]
    },
    {
        "clave": "COMO_GANAR",
        "keywords": ["como", "gano", "ganar", "acumulo", "litros", "cargar"],
        "sugerencias": ["Mi nivel", "Mis puntos", "Catálogo de premios"]
    },
    {
        "clave": "CATALOGO",
        "keywords": ["premio", "premios", "catalogo", "recompensa", "recompensas", "canjear"],
        "sugerencias": ["Mis puntos", "Mis códigos", "Cómo canjear"]
    },
    {
        "clave": "COMO_CANJEAR",
        "keywords": ["canjear", "canje", "redimir", "codigo", "códigos"],
        "sugerencias": ["Catálogo de premios", "Mis códigos", "Mis puntos"]
    },
    {
        "clave": "MIS_CODIGOS",
        "keywords": ["mis", "codigos", "códigos", "canjeado", "canjee", "historial", "mis canjes"],
        "sugerencias": ["Catálogo de premios", "Mis puntos", "Cómo canjear"]
    },
    {
        "clave": "CUANTO_FALTA",
        "keywords": ["falta", "faltan", "me falta", "para", "alcanzar"],
        "sugerencias": ["Catálogo de premios", "Mis puntos"]
    },
    {
        "clave": "PUEDO_CANJEAR",
        "keywords": ["puedo", "puedo canjear", "alcanzo", "me alcanza"],
        "sugerencias": ["Catálogo de premios", "Mis puntos", "Mis códigos"]
    }
]


def detectar_intencion(texto: str):
    norm = normalizar(texto)
    if not norm:
        return None, []

    # Coincidencia directa por keywords
    mejor = None
    mejor_score = 0
    for intent in INTENCIONES:
        score = 0
        for kw in intent["keywords"]:
            kw_norm = normalizar(kw)
            if kw_norm in norm:
                score += 1
        # bonus si varias palabras clave coinciden
        if score > mejor_score:
            mejor_score = score
            mejor = intent
        elif score == mejor_score and mejor_score > 0 and mejor is None:
            mejor = intent

    # Si no hay coincidencia directa, intentar similitud con keywords
    if mejor_score == 0:
        all_kws = []
        kw_to_intent = {}
        for intent in INTENCIONES:
            for kw in intent["keywords"]:
                kn = normalizar(kw)
                if kn and kn not in kw_to_intent:
                    all_kws.append(kn)
                    kw_to_intent[kn] = intent
        # buscar por palabras del mensaje
        palabras = norm.split()
        for p in palabras:
            matches = get_close_matches(p, all_kws, n=1, cutoff=0.8)
            if matches:
                intent = kw_to_intent.get(matches[0])
                if intent:
                    return intent["clave"], intent.get("sugerencias", [])
        return None, []

    if mejor:
        return mejor["clave"], mejor.get("sugerencias", [])
    return None, []
