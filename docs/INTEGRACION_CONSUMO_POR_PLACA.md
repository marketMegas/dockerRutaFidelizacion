# Integración - Envío de consumos por placa

## Objetivo

Permitir que el sistema de despacho/surtidor envíe el consumo en litros asociado a una **placa** hacia la plataforma de fidelización.

## Principios clave

- **Dato principal:** `placa` + `litros`. No es obligatorio enviar cédula ni celular en este endpoint.
- **Formato estricto de placa:** Debe cumplir `^[A-Z]{3}[0-9]{3}$`. Ejemplo: `ABC123`. Únicamente mayúsculas, 3 letras y 3 números.
- **Sin rechazo por falta de vinculación:** Si la placa aún no tiene cédula o celular registrados, **se debe aceptar y guardar el consumo igual**. El rechazo **únicamente** aplica por formato inválido, campos obligatorios o autenticación.
- **Vinculación posterior:** Cuando el cliente se registre en la **aplicación móvil/web** con su cédula y/o celular, esa placa quedará automáticamente asociada a su cuenta y los consumos registrados con anterioridad se le podrán asignar según la lógica de la plataforma.
- **Idempotencia:** Obligatoria por `id_transaccion`.
- **Alcance:** Únicamente **acumular consumo**. El canje de los códigos precargados en el Excel se realiza desde la aplicación autenticada por el cliente.

## Endpoint

```http
POST {BASE_URL}/fid-api/integracion/consumos
```

## Autenticación (máquina a máquina)

```http
X-API-Key: {API_KEY}
Content-Type: application/json
```

## Cuerpo de la petición

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `placa` | `string` | **Sí** | Placa en formato estricto `ABC123` (3 letras + 3 números en mayúsculas). |
| `litros` | `number` | **Sí** | Cantidad despachada en litros. Debe ser mayor a `0`. Acepta decimales (ej. `12.50`). |
| `id_transaccion` | `string` | **Sí** | Identificador único e inmutable del despacho (ticket, consecutivo de surtidor o número de factura). Usado para garantizar idempotencia. |
| `estacion_id` | `string` | Recomendado | Código de la estación donde se realizó el despacho (ej. `EDS-01`). |
| `fecha_hora` | `string` (ISO 8601) | Opcional | Fecha y hora del despacho. Si se omite, la plataforma tomará la fecha/hora de recepción. |

### Ejemplo válido

```json
{
  "placa": "ABC123",
  "litros": 12.50,
  "id_transaccion": "TKT-EDS01-00012345",
  "estacion_id": "EDS-01",
  "fecha_hora": "2025-10-24T14:25:18-05:00"
}
```

## Respuesta exitosa

### Caso 1: Placa YA vinculada a un cliente con cédula y/o celular
```json
{
  "exitoso": true,
  "duplicado": false,
  "id_transaccion": "TKT-EDS01-00012345",
  "placa": "ABC123",
  "litros": 12.50,
  "cliente_vinculado": true,
  "puntos_esta_venta": 12,
  "saldo_puntos": 257,
  "nivel": {
    "clave": "bronce",
    "nombre": "Bronce",
    "multiplicador": 1.0
  },
  "mensaje": "Consumo registrado y puntos acumulados al cliente vinculado a esta placa."
}
```

### Caso 2: Placa SIN cliente vinculado (sin cédula ni celular registrado)
```json
{
  "exitoso": true,
  "duplicado": false,
  "id_transaccion": "TKT-EDS01-00012345",
  "placa": "ABC123",
  "litros": 12.50,
  "cliente_vinculado": false,
  "mensaje": "Consumo registrado correctamente para la placa ABC123. Aún no hay un cliente vinculado con cédula y/o celular. Al registrarse en la aplicación con sus datos, esta placa quedará asociada y podrá ver sus puntos."
}
```

### Caso 3: Transacción ya enviada anteriormente (idempotencia)
```json
{
  "exitoso": true,
  "duplicado": true,
  "id_transaccion": "TKT-EDS01-00012345",
  "placa": "ABC123",
  "litros": 12.50,
  "cliente_vinculado": true,
  "puntos_esta_venta": 12,
  "saldo_puntos": 257,
  "mensaje": "Transacción ya registrada. No se otorgaron puntos duplicados."
}
```

## Errores esperados

| Código | Motivo | Respuesta ejemplo |
|---|---|---|
| `401 Unauthorized` | `X-API-Key` ausente o inválida | `{"detail": "API Key inválida"}` |
| `422 Unprocessable Entity` | Formato de placa incorrecto (minúsculas, guiones, menos/más de 6 caracteres), `litros <= 0`, `litros` no numérico, `id_transaccion` vacío o tipos inválidos. | `{"detail": "La placa debe tener formato ABC123 (3 letras y 3 números, solo mayúsculas)."}` |
| `429 Too Many Requests` | Límite de solicitudes excedido (si aplica) | `{"detail": "Demasiadas solicitudes"}` |

> **Importante:** No debe retornar `404` por el hecho de que la placa no tenga cédula, celular o cliente asociado. Ese escenario es válido y **debe** ser aceptado con `cliente_vinculado: false`.

## Flujo general

1. **Surtidor/TPV** envía `POST {BASE_URL}/fid-api/integracion/consumos` con `placa`, `litros`, `id_transaccion`.
2. **Plataforma** valida formato, autenticación e idempotencia.
3. **Registro**: Se guarda el consumo asociado a la `placa`. Si existe un cliente vinculado a esa placa, se calculan y acumulan puntos. Si no existe, el consumo queda registrado a la placa sin acumular a ningún cliente aún.
4. **App**: El cliente se registra/valida con su **cédula y/o celular**. Al hacerlo, la plataforma vincula esa placa a su cuenta.
5. **Canje**: Ya vinculado, el cliente podrá consultar su saldo y redimir los **códigos precargados desde Excel** directamente desde la aplicación.

## Pruebas rápidas con cURL

```bash
curl -X POST "http://127.0.0.1:8002/fid-api/integracion/consumos" \
  -H "X-API-Key: dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{
        "placa": "ABC123",
        "litros": 12.50,
        "id_transaccion": "TKT-PRUEBA-001",
        "estacion_id": "EDS-01"
      }'
```

## Recomendaciones para el integrador

- **Usar `id_transaccion` estable:** Debe ser único por despacho. En caso de timeout/reintento, **SIEMPRE** enviar el mismo `id_transaccion`.
- **Normalizar a mayúsculas:** Enviar la placa siempre en mayúsculas sin espacios ni guiones.
- **Enviar solo lo necesario:** `cedula`/`celular` **no van** en este endpoint. Son exclusivos del registro/validación en la aplicación.
- **No depender de que la placa exista:** El integrador debe seguir enviando el consumo aunque la plataforma nunca haya visto esa placa antes.
- **Clave única:** La **PLACA** es el dato principal. Consumo en litros es lo que se envía.
