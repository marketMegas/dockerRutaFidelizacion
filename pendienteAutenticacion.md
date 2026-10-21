# Pendiente: cambio de celular del usuario (sin comprometer seguridad)

> Plan futuro. Documento de referencia; no implementado todavía.

## Contexto actual

- Login PWA: placa + OTP por SMS (`api/app/routers/auth.py`); la cuenta está anclada al **teléfono** (único).
- JWT `sub` = id numérico, TTL 12 h; sin invalidación de sesiones.
- El backend ya reemplaza el teléfono "silenciosamente" en `POST /auth/otp/request` (`api/app/routers/auth.py:98-104`) sin verificar la cédula ni el celular viejo; la PWA no lo expone en la UI (`Login.jsx` solo pide teléfono en registro).
- No hay historial de teléfonos, ni edición de teléfono por el admin (`ClientePatchIn` solo acepta `cedula` y `nombre`, `api/app/schemas.py:27-29`).
- El POS (Zencillo) identifica al cliente por teléfono (`api/app/routers/sync.py:21-28`): tras un cambio, la acumulación falla hasta que el POS sepa el nuevo número.

## Opciones

1. **Auto-servicio con doble verificación (recomendada)**: placa + cédula + OTP al nuevo celular (opcional OTP al viejo si aún lo tiene). Reutiliza `generar_otp`/`hash_otp`, SMS y rate limit existentes.
2. **Mínima**: exponer en la UI el cambio con OTP solo al nuevo celular; agregar auditoría + SMS al número viejo ("si no fuiste tú, avisa al grifo").
3. **Asistida por admin** (presencial en el grifo): añadir `telefono` al `ClientePatchIn` con unicidad + auditoría. Cero riesgo remoto, pero requiere que el usuario vaya al grifo.
4. **Híbrida (1 + 3)**: auto-servicio con cédula; si falla (no la sabe / no la registró), cae al flujo admin presencial.

## Seguridad en cualquier opción

- Invalidar tokens vigentes al cambiar (agregar `token_version` al JWT o reducir TTL).
- Rate-limit por cliente además de por placa.
- Historial/auditoría de cambios (cliente_id, teléfono viejo, nuevo, fecha, vía).
- Notificación SMS al número viejo.

## Impacto operativo

- Tras el cambio, el POS sigue acumulando por el teléfono viejo hasta actualizar la sincronización o que el usuario informe el nuevo número en estación.

## Pasos mínimos sugeridos (opción 2)

1. Nuevo endpoint `POST /auth/cambiar-telefono` (placa + OTP viejo o cédula + OTP nuevo).
2. Exponer el formulario en el login/PWA.
3. Tabla `telefono_historial` + escritura al cambiar.
4. SMS al número viejo.
