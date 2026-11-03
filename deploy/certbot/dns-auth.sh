#!/bin/sh
# Hook de certbot para el challenge DNS-01 manual (instancia de prueba).
# Escribe el valor TXT y espera (max 20 min) a que el operador lo cree
# en GoDaddy y marque continuar.
#
# Requiere que los directorios existan en /opt/fidelizacion-glp-prueba/.certbot
set -e
DIR=/opt/fidelizacion-glp-prueba/.certbot
mkdir -p "$DIR"
printf '%s' "$CERTBOT_VALIDATION" > "$DIR/ultimo_txt.txt"
chmod 600 "$DIR/ultimo_txt.txt"
{
  echo "dominio=$CERTBOT_DOMAIN"
  echo "txt=$CERTBOT_VALIDATION"
} > "$DIR/estado.txt"
i=0
while [ ! -f "$DIR/continuar" ]; do
  i=$((i+1))
  if [ "$i" -ge 400 ]; then
    echo "Timeout esperando el TXT manual" >&2
    exit 1
  fi
  sleep 3
done
rm -f "$DIR/continuar"
