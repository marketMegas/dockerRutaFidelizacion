# DNS y TLS para la instancia de PRUEBA

## Contexto
- Instancia de prueba desplegada en el VPS `177.7.49.5` (directorio `/opt/fidelizacion-glp-prueba`).
- Acceso: `https://prueba-fidelizacion.megas.com.co:8443/`.
- Certificado real de **Let's Encrypt** emitido con challenge **DNS-01**, por lo que no ocupa los puertos 80/443 del sitio existente.

## Registro DNS
En el panel DNS del dominio `megas.com.co` (GoDaddy):

| Tipo | Nombre | Valor | TTL |
|---|---|---|---|
| A | `prueba-fidelizacion` | `177.7.49.5` | 3600 |

Dominio completo resultante: `prueba-fidelizacion.megas.com.co` → `177.7.49.5`.

## Certificado (Let's Encrypt, DNS-01 manual)
- El certificado se emitió con `certbot` en modo `--manual --preferred-challenges dns`.
- Material en `/.certbot/config/live/prueba-fidelizacion.megas.com.co/` del VPS.
- Caddy consume copias en `.auth/prueba.crt` y `.auth/prueba.key` (montadas en `/etc/caddy/tls`).
- La renovación es semiautomática (el TXT se crea a mano en GoDaddy):
  1. Ejecutar `sh /opt/fidelizacion-glp-prueba/.certbot/renovar-cert.sh`.
  2. Crear/actualizar el TXT `_acme-challenge.prueba-fidelizacion` con el valor que muestra el script.
  3. Verificar con `nslookup -type=TXT _acme-challenge.prueba-fidelizacion.megas.com.co` y presionar Enter.
  4. El script instala el certificado y reinicia Caddy.
- `autorenew = False` en la configuración de certbot: la auto-renovación está desactivada porque el challenge DNS es manual (evita que el timer quede colgado esperando el TXT).

## Notas
- El DNS no es necesario para acceder por IP, pero sí para el certificado real.
- Basic Auth: la PWA pide contraseña solo al abrir; la API directa la exige; el panel queda sin Basic Auth (usa su propio login).
