#!/usr/bin/env bash
set -euo pipefail

# El .env y los respaldos contienen secretos y datos personales.
umask 077

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"
ENV_FILE="$APP_DIR/.env"
ACCION="${1:-up}"

cd "$APP_DIR"

#si hay env lo usa de lo contrario crea uno nuevo con valores por defecto y SECRET_KEY aleatoria 

preparar_env() {
  if [ ! -f "$ENV_FILE" ]; then
    cp .env.example .env
    local secret redis_pass
    secret="$(openssl rand -hex 32)"
    redis_pass="$(openssl rand -hex 24)"
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${secret}|" .env
    sed -i "s|^DEBUG=.*|DEBUG=False|" .env
    sed -i "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=${redis_pass}|" .env
    sed -i "s|^REDIS_URL=.*|REDIS_URL=redis://:${redis_pass}@redis:6379/0|" .env
    chmod 600 "$ENV_FILE"
    echo ">> Creado .env nuevo con SECRET_KEY y REDIS_PASSWORD aleatorias."
    echo ">> IMPORTANTE: edita .env y cambia SYNC_API_KEY, POSTGRES_PASSWORD, ADMIN_PASSWORD y SMS_PROVIDER."
  else
    chmod 600 "$ENV_FILE"
    echo ">> Usando .env existente."
  fi
}

# Genera el env minimo del conector a partir de .env (minimo privilegio).
preparar_env_conector() {
  local salida="$APP_DIR/.env.connector"
  umask 077
  {
    grep -E '^(SYNC_API_KEY|ESTACION_ID|ZENCILLO_MODO|ZENCILLO_API_URL|ZENCILLO_API_KEY|ZENCILLO_ARCHIVO|POLL_SEGUNDOS|COLA_ARCHIVO)=' "$ENV_FILE" || true
    grep -qE '^POLL_SEGUNDOS=' "$ENV_FILE" || echo "POLL_SEGUNDOS=30"
  } > "$salida.tmp"
  mv "$salida.tmp" "$salida"
  chmod 600 "$salida"
}

cargar_env() {
  if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . <(tr -d '\r' < "$ENV_FILE")
    set +a
  fi
}

validar_env() {
  local faltantes=()
  local var
  for var in POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB DATABASE_URL REDIS_URL REDIS_PASSWORD \
    SECRET_KEY ADMIN_USER ADMIN_PASSWORD SYNC_API_KEY CORS_ORIGINS SMS_PROVIDER ESTACION_ID; do
    if [ -z "${!var:-}" ]; then
      faltantes+=("$var")
    fi
  done
  if [ ${#faltantes[@]} -gt 0 ]; then
    echo ">> ERROR: faltan variables en .env: ${faltantes[*]}" >&2
    exit 1
  fi

  local inseguras=()
  local secret="${SECRET_KEY:-}"
  local admin="${ADMIN_PASSWORD:-}"
  local sync="${SYNC_API_KEY:-}"
  local cors="${CORS_ORIGINS:-}"
  local sms
  sms="$(printf '%s' "${SMS_PROVIDER:-}" | tr '[:upper:]' '[:lower:]')"
  local debug
  debug="$(printf '%s' "${DEBUG:-False}" | tr '[:upper:]' '[:lower:]')"

  if [ "$secret" = "cambiar_por_openssl_rand_base64_48" ] || [ "$secret" = "secretkeyReemplazarEnProduccion" ]; then
    inseguras+=("SECRET_KEY (valor de plantilla)")
  fi
  if [ ${#secret} -lt 32 ]; then
    inseguras+=("SECRET_KEY (menos de 32 caracteres)")
  fi
  if [ "$admin" = "admin123" ] || [ ${#admin} -lt 10 ]; then
    inseguras+=("ADMIN_PASSWORD (plantilla o menos de 10 caracteres)")
  fi
  if [ "${POSTGRES_PASSWORD:-}" = "fidelizacion" ]; then
    inseguras+=("POSTGRES_PASSWORD (valor de plantilla)")
  fi
  if [ "${REDIS_PASSWORD:-}" = "cambiar_por_openssl_rand_hex_24" ] || [ ${#REDIS_PASSWORD} -lt 16 ]; then
    inseguras+=("REDIS_PASSWORD (plantilla o menos de 16 caracteres)")
  fi
  if [ -n "${REDIS_PASSWORD:-}" ] && [[ "${REDIS_URL:-}" != *"${REDIS_PASSWORD}"* ]]; then
    inseguras+=("REDIS_URL no incluye REDIS_PASSWORD")
  fi
  if [ "$sync" = "dev-api-key" ] || [ ${#sync} -lt 16 ]; then
    inseguras+=("SYNC_API_KEY (plantilla o menos de 16 caracteres)")
  fi
  if [ "$cors" = "*" ]; then
    inseguras+=("CORS_ORIGINS (no puede ser *)")
  fi
  case "$debug" in
    true | 1 | yes | on) inseguras+=("DEBUG (debe ser False)") ;;
  esac
  if [ "$sms" = "debug" ]; then
    inseguras+=("SMS_PROVIDER (debe ser 'http' en produccion)")
  fi

  if [ ${#inseguras[@]} -gt 0 ]; then
    echo ">> ERROR: corrige estos valores de .env antes de desplegar:" >&2
    printf '   - %s\n' "${inseguras[@]}" >&2
    exit 1
  fi
}

cargar_env

case "$ACCION" in
  up)
    preparar_env
    cargar_env
    validar_env
    preparar_env_conector
    echo ">> Construyendo y levantando contenedores..."
    docker compose -f "$COMPOSE_FILE" up -d --build --wait --wait-timeout 240
    echo
    docker compose -f "$COMPOSE_FILE" ps
    echo
    if curl -fsS http://127.0.0.1:8002/health; then
      echo
      echo ">> API operativa en http://127.0.0.1:8002"
    else
      echo ">> La API aun no responde. Revisa: docker compose -f docker-compose.prod.yml logs -f api"
    fi
    ;;
  down)
    docker compose -f "$COMPOSE_FILE" down
    ;;
  update)
    git pull --ff-only || echo ">> Sin repositorio git; continuando con el codigo local."
    cargar_env
    validar_env
    preparar_env_conector
    docker compose -f "$COMPOSE_FILE" up -d --build --wait --wait-timeout 240
    docker compose -f "$COMPOSE_FILE" ps
    ;;
  niveles)
    docker compose -f "$COMPOSE_FILE" exec -T api python -m scripts.actualizar_niveles
    ;;
  logs)
    docker compose -f "$COMPOSE_FILE" logs -f "${2:-}"
    ;;
  backup)
    mkdir -p backups
    stamp="$(date +%Y%m%d-%H%M%S)"
    docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "${POSTGRES_USER:-fidelizacion}" "${POSTGRES_DB:-fidelizacion}" > "backups/fidelizacion-${stamp}.sql"
    chmod 600 "backups/fidelizacion-${stamp}.sql"
    echo ">> Respaldo en backups/fidelizacion-${stamp}.sql"
    if docker compose -f "$COMPOSE_FILE" exec -T api sh -c 'cat "${CATALOGO_PATH:-/app/data/catalogo.json}"' > "backups/catalogo-${stamp}.json"; then
      chmod 600 "backups/catalogo-${stamp}.json"
      echo ">> Catalogo respaldado en backups/catalogo-${stamp}.json"
    else
      rm -f "backups/catalogo-${stamp}.json"
      echo ">> No se pudo respaldar el catalogo (la API no esta corriendo?)"
    fi
    ;;
  *)
    echo "Uso: deploy.sh [up|down|update|niveles|logs|backup]"
    exit 1
    ;;
esac
