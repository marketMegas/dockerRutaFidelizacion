# -*- coding: utf-8 -*-
from typing import Dict, Any, List, Optional
from difflib import get_close_matches

from sqlalchemy.orm import Session

from app.models import Cliente, Canje
from app.services import catalogo
from app.services.chatbot.rules import detectar_intencion, normalizar


class ChatbotService:
    def __init__(self, db: Session, cliente: Cliente):
        self.db = db
        self.cliente = cliente

    def _obtener_catalogo(self) -> Dict[str, Any]:
        try:
            return catalogo.leer()
        except Exception:
            return {"premios": [], "niveles": []}

    def _obtener_canjes(self) -> List[Canje]:
        try:
            return (
                self.db.query(Canje)
                .filter(Canje.cliente_id == self.cliente.id)
                .order_by(Canje.id.desc())
                .all()
            )
        except Exception:
            return []

    def _obtener_nivel_info(self, cat: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        niveles = cat.get("niveles") or []
        if not niveles:
            return None
        # Intentar determinar nivel actual - el cliente tiene nivel? En el modelo no se ve campo nivel directo
        # Pero el frontend usa NivelPanel con cliente; podemos inferir por reglas o mostrar info general
        # Por simplicidad, mostrar el rango/niveles disponibles y mencionar multiplicador
        return {"niveles": niveles}

    def procesar_mensaje(self, mensaje: str) -> Dict[str, Any]:
        intent, sugerencias = detectar_intencion(mensaje)
        cat = self._obtener_catalogo()
        premios = [p for p in (cat.get("premios") or []) if p.get("activo", True)]
        canjes = self._obtener_canjes()
        niveles = cat.get("niveles") or []

        if intent == "SALUDO":
            nombre = self.cliente.nombre or "cliente"
            respuesta = f"Hola {nombre}. Puedo informarte sobre tus puntos, nivel, premios y códigos canjeados. ¿En qué te ayudo?"
            return {"respuesta": respuesta, "sugerencias": sugerencias or ["Mis puntos", "Mi nivel", "Catálogo de premios", "Mis códigos"]}

        if intent == "SALDO_PUNTOS":
            pts = self.cliente.puntos or 0
            respuesta = f"Tienes {pts:,} puntos disponibles.".replace(",", ".")
            return {"respuesta": respuesta, "sugerencias": sugerencias or ["Mi nivel", "Catálogo de premios", "Mis códigos"]}

        if intent == "NIVEL":
            # Mostrar info de niveles
            if not niveles:
                respuesta = "No hay información de niveles disponible en este momento."
            else:
                partes = []
                for n in niveles:
                    clave = n.get("clave", "")
                    nombre_n = n.get("nombre", clave)
                    mult = n.get("multiplicador", 1)
                    minimo = n.get("minimo", 0)
                    partes.append(f"- {nombre_n} (×{mult}): desde {minimo} litros/mes")
                respuesta = "Niveles del programa:\n" + "\n".join(partes) + "\n\nTu multiplicador se aplica según tus litros acumulados en el mes."
            return {"respuesta": respuesta, "sugerencias": sugerencias or ["Cómo gano puntos", "Mis puntos", "Catálogo de premios"]}

        if intent == "COMO_GANAR":
            respuesta = "Ganas puntos por cada litro cargado. El nivel (Arranque, Plata, Oro, Diamante) multiplica los puntos según tus litros del mes. Puedes ver tu nivel y multiplicador en la pantalla de inicio."
            return {"respuesta": respuesta, "sugerencias": sugerencias or ["Mi nivel", "Mis puntos", "Catálogo de premios"]}

        if intent == "CATALOGO":
            if not premios:
                respuesta = "No hay premios disponibles en este momento."
                return {"respuesta": respuesta, "sugerencias": sugerencias or ["Mis puntos", "Mis códigos"]}
            lineas = []
            for p in premios[:10]:  # limitar para no hacer respuesta muy larga
                clave = p.get("clave")
                nombre = p.get("nombre", clave)
                costo = p.get("costo_puntos", 0)
                disp = p.get("codigos_disponibles", 0)
                estado = "Disponible" if disp > 0 else "Agotado"
                lineas.append(f"- {nombre} - {costo:,} pts ({estado})".replace(",", "."))
            respuesta = "Premios disponibles:\n" + "\n".join(lineas)
            if len(premios) > 10:
                respuesta += f"\n\nY {len(premios)-10} premios más en la sección Recompensas."
            return {"respuesta": respuesta, "sugerencias": sugerencias or ["Mis puntos", "Mis códigos", "Cómo canjear"]}

        if intent == "COMO_CANJEAR":
            respuesta = "Para canjear: ve a Recompensas, elige el premio que quieras, toca Canjear. Si tienes puntos suficientes y hay códigos disponibles, recibirás un código al instante. Lo puedes copiar o compartir desde 'Mis códigos'."
            return {"respuesta": respuesta, "sugerencias": sugerencias or ["Catálogo de premios", "Mis códigos", "Mis puntos"]}

        if intent == "MIS_CODIGOS":
            if not canjes:
                respuesta = "Aún no has canjeado ningún premio. Puedes ver el catálogo en Recompensas."
                return {"respuesta": respuesta, "sugerencias": sugerencias or ["Catálogo de premios", "Mis puntos"]}
            lineas = []
            for c in canjes[:8]:
                premio = c.premio_nombre or c.premio_clave
                codigo = c.codigo or ""
                # mostrar código completo
                lineas.append(f"- {premio}: {codigo}")
            respuesta = "Tus códigos canjeados:\n" + "\n".join(lineas)
            if len(canjes) > 8:
                respuesta += f"\n\nTienes {len(canjes)} canjes en total. Los puedes ver todos en Recompensas > Mis códigos."
            return {"respuesta": respuesta, "sugerencias": sugerencias or ["Catálogo de premios", "Mis puntos", "Cómo canjear"]}

        if intent == "CUANTO_FALTA":
            pts = self.cliente.puntos or 0
            norm = normalizar(mensaje)
            # intentar encontrar premio mencionado
            mejor_premio = None
            mejor_score = 0
            for p in premios:
                nombre_n = normalizar(p.get("nombre", ""))
                if not nombre_n:
                    continue
                # buscar similitud con nombre o palabras
                if nombre_n in norm:
                    mejor_premio = p
                    break
                # similitud por palabras
                palabras_p = nombre_n.split()
                score = 0
                for wp in palabras_p:
                    if wp in norm:
                        score += 1
                if score > mejor_score and score > 0:
                    mejor_score = score
                    mejor_premio = p
            if not mejor_premio:
                # listar opciones
                if not premios:
                    respuesta = "No hay premios disponibles para calcular."
                else:
                    lineas = [f"- {p.get('nombre')} ({p.get('costo_puntos')} pts)" for p in premios[:5]]
                    respuesta = "Dime para cuál premio quieres saber cuánto te falta. Opciones:\n" + "\n".join(lineas)
                return {"respuesta": respuesta, "sugerencias": sugerencias or ["Catálogo de premios", "Mis puntos"]}
            costo = int(mejor_premio.get("costo_puntos") or 0)
            if pts >= costo:
                respuesta = f"Ya tienes suficientes puntos para '{mejor_premio.get('nombre')}' ({costo} pts). Puedes canjearlo en Recompensas."
            else:
                falta = costo - pts
                respuesta = f"Te faltan {falta:,} puntos para '{mejor_premio.get('nombre')}' ({costo} pts). Tienes {pts:,} pts.".replace(",", ".")
            return {"respuesta": respuesta, "sugerencias": sugerencias or ["Catálogo de premios", "Mis códigos"]}

        if intent == "PUEDO_CANJEAR":
            pts = self.cliente.puntos or 0
            norm = normalizar(mensaje)
            mejor_premio = None
            for p in premios:
                nombre_n = normalizar(p.get("nombre", ""))
                if nombre_n and nombre_n in norm:
                    mejor_premio = p
                    break
            if not mejor_premio:
                respuesta = "Dime el nombre del premio para verificar si puedes canjearlo. Puedes verlos en Recompensas."
                return {"respuesta": respuesta, "sugerencias": sugerencias or ["Catálogo de premios", "Mis puntos"]}
            costo = int(mejor_premio.get("costo_puntos") or 0)
            disp = int(mejor_premio.get("codigos_disponibles") or 0)
            if disp <= 0:
                respuesta = f"'{mejor_premio.get('nombre')}' está agotado en este momento."
            elif pts >= costo:
                respuesta = f"Sí, puedes canjear '{mejor_premio.get('nombre')}' ({costo} pts). Tienes {pts} pts disponibles."
            else:
                falta = costo - pts
                respuesta = f"No te alcanza aún. Te faltan {falta} pts para '{mejor_premio.get('nombre')}' ({costo} pts)."
            return {"respuesta": respuesta, "sugerencias": sugerencias or ["Catálogo de premios", "Mis códigos"]}

        # Fallback genérico
        respuesta = "Puedo informarte sobre: tus puntos, nivel, premios disponibles, mis códigos canjeados y cómo canjear. Prueba preguntando: '¿Cuántos puntos tengo?' o '¿Qué premios hay?'"
        return {"respuesta": respuesta, "sugerencias": ["Mis puntos", "Mi nivel", "Catálogo de premios", "Mis códigos"]}
