#!/bin/sh
# Renovacion semiautomatica del certificado (challenge DNS-01 en GoDaddy).
# Uso en el VPS:  sh /opt/fidelizacion-glp-prueba/.certbot/renovar-cert.sh
#
# Asume que la instancia vive en /opt/fidelizacion-glp-prueba y que los
# hooks dns-auth.sh / dns-cleanup.sh estan en .certbot/.
set -e
BASE=/opt/fidelizacion-glp-prueba
DIR=$BASE/.certbot
DOM=prueba-fidelizacion.megas.com.co

rm -f "$DIR/estado.txt" "$DIR/continuar"

setsid certbot certonly --manual --preferred-challenges dns -d "$DOM" \
  --manual-auth-hook "$DIR/dns-auth.sh" \
  --manual-cleanup-hook "$DIR/dns-cleanup.sh" \
  --config-dir "$DIR/config" --work-dir "$DIR/work" --logs-dir "$DIR/logs" \
  --agree-tos -m admin@megas.com.co --no-eff-email --non-interactive \
  < /dev/null > "$DIR/certbot.log" 2>&1 &
CERTBOT_PID=$!

echo "Certbot iniciado (PID $CERTBOT_PID). Esperando el valor TXT..."
i=0
while [ ! -f "$DIR/estado.txt" ]; do
  i=$((i+1))
  if [ "$i" -ge 60 ]; then
    echo "No se genero el TXT. Revisa $DIR/certbot.log"
    exit 1
  fi
  sleep 2
done
. "$DIR/estado.txt"

echo
echo "=== Crea/actualiza en GoDaddy el registro TXT ==="
echo "  Type : TXT"
echo "  Name : _acme-challenge.prueba-fidelizacion"
echo "  Value: $txt"
echo "  TTL  : 300"
echo
echo "Verifica con: nslookup -type=TXT _acme-challenge.prueba-fidelizacion.megas.com.co"
echo

printf "Cuando el TXT ya este creado y propagado, presiona Enter para continuar..."
read _ || true
touch "$DIR/continuar"

wait "$CERTBOT_PID"
rc=$?
echo "Certbot termino con codigo $rc"

if [ "$rc" -eq 0 ]; then
  cp "$DIR/config/live/$DOM/fullchain.pem" "$BASE/.auth/prueba.crt"
  cp "$DIR/config/live/$DOM/privkey.pem" "$BASE/.auth/prueba.key"
  chmod 644 "$BASE/.auth/prueba.crt"
  chmod 600 "$BASE/.auth/prueba.key"
  ( cd "$BASE" && docker compose -f docker-compose.prueba.yml restart caddy )
  echo "Certificado renovado e instalado en Caddy."
fi

exit "$rc"
