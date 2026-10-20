# Sistema de Fidelizacion GLP

Programa de puntos para una estacion de GLP (autogas): los clientes acumulan puntos por cada
litro que cargan, se identifican con la placa de su vehiculo, y canjean recompensas presentando
su cedula en la estacion.
La administracion de la estacion gestiona reglas, recompensas, clientes y reportes.

Pensado para desplegarse en el VPS Hostinger (AlmaLinux 9 + CyberPanel/OpenLiteSpeed) junto a
los otros sitios del servidor, y para arrancar en modo simulado mientras se define la
integracion con Zencillo.

## Componentes

| Carpeta               | Que es                                                       | Stack                       | Puerto (host) |
|-----------------------|-------------------------------------------------------------|-----------------------------|---------------|
| `api/`                | Backend: reglas, puntos (ledger), auth OTP/JWT, admin        | FastAPI + SQLAlchemy + Postgres | 127.0.0.1:8002 |
| `panel/`              | Panel de administracion (React SPA)                          | React 18 + Vite + nginx     | 127.0.0.1:5139 |
| `pwa/`                | App del cliente (instalable, muestra saldo)                  | React 18 + Vite + nginx     | 127.0.0.1:5140 |
| `connector-zencillo/` | Trae ventas desde Zencillo (o simulador) hacia la API        | Python + requests           | -             |
| `deploy/`             | Script de despliegue y plantillas de LiteSpeed               | bash                        | -             |
| `db`                  | PostgreSQL 17                                                | postgres:17-alpine          | 127.0.0.1:5433 |
| `redis`               | Cache / support                                              | redis:7-alpine              | interno       |

Flujo de puntos: el conector envia una venta a `POST /fid-api/sync/venta` con el telefono del
cliente y la placa del vehiculo (la ultima placa queda guardada en el cliente); la API
calcula puntos con la regla vigente y registra un movimiento inmutable
en el ledger. El panel y la PWA leen saldos y movimientos desde la misma API.

El ledger nunca borra movimientos: los canjes y reversos se anotan como movimientos nuevos. Un
reverso que dejaria el saldo en negativo se rechaza.

## Requisitos

- Docker Desktop (local) / Docker Engine + Compose (VPS)
- Para desarrollo sin Docker: Python 3.12+, Node 20+

## Desarrollo local

### Opcion A: todo con Docker

```bash
cp .env.example .env
docker compose up -d --build
```

- PWA cliente: http://localhost:5140 — barra superior con logo y secciones `Inicio`, `Funcionamiento`,
  `Recompensas`, `Ayuda`; con sesion activa el boton cambia a `Salir` y aparece la barra inferior
  `Mis datos` / `Historial`
- Panel admin: http://localhost:5139/panel/  (usuario `admin` / `admin123` por defecto)
- API: http://localhost:8002/health
- Conector (opcional, perfil aparte): `docker compose --profile conector up -d`

El acceso del cliente es por **placa** (3 letras seguidas de 3 numeros, ej. `ABC123`, sin espacios
ni guiones; se valida antes de registrar). En la PWA el usuario escribe la placa de su vehiculo;
si ya existe le enviamos el codigo al celular registrado, y si no existe se auto-registra con
**cedula obligatoria** + celular + nombre. La placa sirve para entrar y acumular; el
**reclamo de recompensas se hace presentando la cedula** en la estacion (el panel busca el canje
por cedula y lo marca entregado).
Un mismo **numero de celular puede tener varias placas** registradas: la cuenta y el saldo de
puntos son del celular, y cada vehiculo se asocia a esa cuenta (al iniciar sesion con la placa
nueva o desde el panel). El historial y los canjes son unicos por cuenta.
Los clientes creados antes de exigir cedula pueden agregarla en `Mis datos` (PWA) o desde el
panel (`PATCH /admin/clientes/{id}`); sin cedula no pueden reclamar canjes.
Con `DEBUG=True` (y `SMS_PROVIDER=debug`) la API devuelve el codigo OTP en la respuesta
(`debug_codigo`), util para probar el login sin SMS. En produccion se fija `DEBUG=False` y se
configura `SMS_PROVIDER`/`SMS_API_URL` para enviar el codigo por SMS
(punto de extension: `api/app/services/sms.py`).

### Opcion B: servicios por separado

API (SQLite, sin Postgres):

```bash
cd api
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements-dev.txt
ruff check .
pytest
uvicorn app.main:app --reload --port 8000
```

Panel y PWA:

```bash
cd panel && npm install && npm run dev   # http://localhost:5174/panel/
cd pwa   && npm install && npm run dev   # http://localhost:5175
```

Conector:

```bash
cd connector-zencillo
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python conector.py menu
```

## API (resumen)

Prefijo `API_PREFIX=/fid-api`.

- `POST /fid-api/auth/identificar` — consulta si la placa existe (y cel enmascarado).
- `POST /fid-api/auth/otp/request` y `POST /fid-api/auth/otp/verify` — login del cliente por placa
  (auto-registro; `cedula` obligatoria al crear la cuenta, validada como 6 a 10 numeros).
- `POST /fid-api/auth/admin` — login del panel.
- `GET  /fid-api/clientes/me`, `/me/movimientos` — datos del cliente autenticado (`placas`, `cedula`).
- `PATCH /fid-api/clientes/me` — el cliente agrega/actualiza su cedula (duplicada = 409).
- `POST /fid-api/sync/venta` — ingesta de ventas (header `X-API-Key`), idempotente por `id_externo`.
- `GET  /fid-api/recompensas`, `POST /fid-api/canjes`, `GET /fid-api/canjes/mis` — recompensas y canjes.
- `GET  /fid-api/config` — publico; tasa vigente (`puntos_por_litro`) para mostrar equivalencias en la PWA.
- `GET  /fid-api/admin/resumen|ventas|clientes|canjes|reglas|recompensas` y endpoints de gestion/reverso.
  `GET /admin/canjes?q=<cedula>` filtra los canjes por cedula del cliente.
- `PATCH /fid-api/admin/clientes/{id}` — editar nombre/cedula del cliente desde el panel.
- `POST /fid-api/admin/reglas` y `PUT /fid-api/admin/reglas/{id}` — crear y editar reglas (edicion parcial:
  solo se pisan los campos enviados; valida nombre duplicado con 409 y `desde > hasta` con 400).
- `POST /fid-api/admin/recompensas` y `PUT /fid-api/admin/recompensas/{id}` — crear y editar recompensas.
  El campo `imagen` es la **URL** (max. 500) de la foto de referencia que se muestra en la tarjeta
  de la PWA; el backend no almacena archivos, la copian/pegan en el panel. `null` muestra un
  bloque de rayas de respaldo.

Documentacion interactiva: `/docs`.

## Despliegue en el VPS (fidelizacion.megas.com.co)

Servidor: AlmaLinux 9 (SELinux enforcing), CyberPanel + OpenLiteSpeed en 443, firewalld.
Docker y Compose ya instalados.

### 1. DNS

Crea un registro A: `fidelizacion.megas.com.co` -> `177.7.49.5`.

### 2. Subir el codigo

```bash
mkdir -p /opt/fidelizacion-glp
# copiar el proyecto (git clone o rsync/scp) a /opt/fidelizacion-glp
cd /opt/fidelizacion-glp
```

### 3. Variables de entorno y arranque

```bash
cp .env.example .env
nano .env
```

Valores a cambiar antes de produccion:

- `SECRET_KEY`: cadena aleatoria larga (`openssl rand -base64 48`). El script la genera si falta.
- `SYNC_API_KEY`: clave que usara el conector. Debe coincidir con la del conector.
- `POSTGRES_PASSWORD`: password fuerte de la base de datos.
- `ADMIN_PASSWORD`: cambia el `admin123`.
- `DEBUG=False`.
- `ZENCILLO_MODO=simulador` al inicio.
- `CORS_ORIGINS`: en produccion deja SOLO el dominio, p.ej.
  `CORS_ORIGINS=https://fidelizacion.megas.com.co` (la plantilla trae ademas los puertos
  de desarrollo).
- `ADMIN_RATE_MAX` / `ADMIN_RATE_VENTANA`: limite de intentos de login del panel admin por IP
  (por defecto 10 intentos / 900 s).

Luego:

```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh up
```

Esto construye y levanta los contenedores y verifica `http://127.0.0.1:8002/health`.
Comandos utiles: `./deploy/deploy.sh logs`, `./deploy/deploy.sh update`, `./deploy/deploy.sh down`,
`./deploy/deploy.sh backup`.

### 4. Publicar el subdominio en OpenLiteSpeed (CyberPanel)

1. En CyberPanel crea el website `fidelizacion.megas.com.co`.
2. Registra los tres proxies en el vhost (ver `deploy/litespeed-vhost.example.conf`):
   API `127.0.0.1:8002`, panel `127.0.0.1:5139`, PWA `127.0.0.1:5140`.
3. Pega las reglas de rewrite de `deploy/htaccess-fidelizacion.txt` en
   *Websites > fidelizacion.megas.com.co > Rewrite Rules*. Enrutado:
   `/fid-api/` -> API, `/panel/` -> panel, `/` -> PWA.

### 5. SSL

Emite el certificado con el flujo DNS de CyberPanel (Let's Encrypt via acme.sh + PowerDNS
interno) para `fidelizacion.megas.com.co`, o desde el panel con *Issue SSL*. Verifica en
`https://fidelizacion.megas.com.co`.

### 6. Firewall / SELinux

Los contenedores se enlazan a `127.0.0.1`, así que no hace falta abrir puertos nuevos en
firewalld (solo 80/443/SSH). OpenLiteSpeed llega a los contenedores por loopback; no se
requiere desactivar SELinux.

### 7. Respaldo de base de datos

`./deploy/deploy.sh backup` genera un volcado en `backups/`. Programalo en cron si quieres
respaldos automaticos.

### 8. Endurecimiento: pendientes post-despliegue

Ya estan activos: rate-limit del login admin por IP (`ADMIN_RATE_MAX`/`ADMIN_RATE_VENTANA`),
CORS explicito (`CORS_ORIGINS`) y cabeceras de seguridad en `pwa/nginx.conf` y
`panel/nginx.conf` (`nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`).

Quedan **dos pasos manuales** que se hacen solo despues de confirmar SSL en el VPS
(ambos afectan a los `nginx.conf` de panel y PWA):

1. **HSTS**: agregar la cabecera, por ejemplo
   `add_header Strict-Transport-Security "max-age=31536000" always;`
   en cada `server {}`. Hasta ahora se omitio a proposito para no arriesgar un bloqueo
   de HTTPS si el certificado falla.

2. **CSP en modo estricto**: la CSP actual esta en modo `Report-Only`
   (`Content-Security-Policy-Report-Only`, no bloquea). Revisa la consola del navegador
   (PWA y panel) durante unos dias y, si no hay reportes, cambiarla a estricta:
   reemplazar `Content-Security-Policy-Report-Only` por `Content-Security-Policy` en
   `pwa/nginx.conf` y `panel/nginx.conf`.

## Integracion con Zencillo

Al inicio corre en `ZENCILLO_MODO=simulador`. Para conectar con la plataforma de despacho,
mira `connector-zencillo/README.md`: ahi esta la lista exacta de datos y accesos que hay que
solicitar a Zencillo (endpoint de ventas, autenticacion, contrato de campos e identificador
unico por venta). La facturacion electronica DIAN sigue en manos de Zencillo; este sistema solo
consume las ventas para calcular puntos.

## Pruebas

```bash
cd api && ruff check . && pytest
```

La suite cubre el motor de reglas, el ledger (acumulacion, canje, reverso, saldo insuficiente),
las cuentas multivehiculo (varias placas por celular, cedula obligatoria y su gestion) y los
endpoints principales a traves de HTTP.
# dockerRutaFidelizacion
