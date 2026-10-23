# Conector Zencillo

Trae las ventas de combustible desde Zencillo (o desde un simulador) hacia la API de
fidelizacion y acumula puntos por la **placa** del vehiculo. La API identifica al cliente dueno
de la placa; el telefono es opcional y solo sirve para asociar una placa nueva.

El conector es tolerante a fallos: si la API de fidelizacion no responde, la venta se guarda
en una cola offline (`cola_offline.json`) y se reenvia automaticamente cuando vuelve la
conexion. La API deduplica por `id_externo`, asi que reintentar nunca genera puntos dobles.

## Modos (`ZENCILLO_MODO`)

| Modo        | Que hace                                                                 |
|-------------|--------------------------------------------------------------------------|
| `simulador` | Ventas manuales por consola o menu. Ideal para arrancar sin integracion. |
| `api`       | Consulta la API REST de Zencillo en la nube cada `POLL_SEGUNDOS`.        |
| `archivos`  | Lee un export plano (CSV) que Zencillo deja en disco o entrega.          |

## Uso rapido (simulador)

```bash
pip install -r requirements.txt
copy .env.example .env

python conector.py menu
python conector.py simular --litros 12.5 --placa ABC123
python conector.py simular --litros 12.5 --placa ABC123 --telefono 3001234567
python conector.py cola
python conector.py sincronizar
```

## Modo api / archivos (daemon)

```bash
set ZENCILLO_MODO=api
python conector.py daemon
```

Para `archivos`, define `ZENCILLO_ARCHIVO=ventas_zencillo.csv`. El conector recuerda que
filas ya proceso en `ventas_zencillo.csv.procesados.json`, por lo que puede leer el mismo
archivo repetidas veces sin duplicar.

## Que solicitar a Zencillo para la integracion

La integracion definitiva depende del modulo/API que Zencillo habilite. Pedir por escrito:

1. **Modulo de fidelizacion / API de ventas**: si la cuenta no tiene el modulo habilitado,
   confirmar si se licencia aparte o si se puede consumir la API de ventas general.
2. **Autenticacion**: tipo de credencial (API key, Basic, token OAuth), y endpoint base.
3. **Endpoint de ventas**: URL que devuelve las ventas/despachos, con que frecuencia se
   actualiza y por que campo filtrar por fecha/estacion.
4. **Contrato de campos por venta** (nombres reales y formatos):
   - `id_factura` (identificador unico e inmutable) -> se usa como `id_externo`.
   - `fecha_hora` de la venta.
   - `placa` / vehiculo.
   - `producto` (GLP).
   - `volumen_lt` en litros (confirmar unidad).
   - `precio` unitario y `valor_total`.
   - `islero` / despachador (opcional, para auditoria).
   - Identificacion del cliente si Zencillo la captura (telefono) — opcional,
      normalmente el cliente se identifica en la PWA con su placa/telefono.
5. **Webhooks**: si ofrecen notificacion push de venta (mejor que polling), pedir contrato.
6. **Ambiente de pruebas** y limites de peticiones.

Los campos se mapean en `fuentes.py` (`CAMPOS`), donde ya se aceptan varios nombres
alternativos. Si Zencillo entrega nombres distintos, basta agregar el alias ahi.

## Fuera de alcance

La facturacion electronica DIAN no la maneja este sistema: Zencillo (o el software de
facturacion de la estacion) la sigue gestionando. Este servicio solo consume las ventas ya
registradas para calcular puntos.
