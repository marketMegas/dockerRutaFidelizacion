#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"
ENV_FILE="$APP_DIR/.env"
ACCION="${1:-up}"

cd "$APP_DIR"

preparar_env() {
  if [ ! -f "$ENV_FILE" ]; then
    cp .env.example .env
    local secret
    secret="$(openssl rand -base64 48 | tr -d '\n/+=+')"
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${secret}|" .env
    sed -i "s|^DEBUG=.*|DEBUG=False|" .env
    echo ">> Creado .env nuevo con SECRET_KEY aleatoria."
    echo ">> IMPORTANTE: edita .env y cambia SYNC_API_KEY, POSTGRES_PASSWORD y ADMIN_PASSWORD."
  else
    echo ">> Usando .env existente."
  fi
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
  for var in POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB DATABASE_URL REDIS_URL SECRET_KEY ESTACION_ID; do
    if [ -z "${!var:-}" ]; then
      faltantes+=("$var")
    fi
  done
  if [ ${#faltantes[@]} -gt 0 ]; then
    echo ">> ERROR: faltan variables en .env: ${faltantes[*]}" >&2
    exit 1
  fi

  local inseguras=()
  [ "${SECRET_KEY:-}" = "secretkeyReemplazarEnProduccion" ] && inseguras+=("SECRET_KEY")
  [ "${POSTGRES_PASSWORD:-}" = "fidelizacion" ] && inseguras+=("POSTGRES_PASSWORD")
  [ "${ADMIN_PASSWORD:-}" = "admin123" ] && inseguras+=("ADMIN_PASSWORD")
  [ "${SYNC_API_KEY:-}" = "dev-api-key" ] && inseguras+=("SYNC_API_KEY")
  [ "${CORS_ORIGINS:-}" = "*" ] && inseguras+=("CORS_ORIGINS")
  [ "${DEBUG:-False}" = "True" ] && inseguras+=("DEBUG")
  if [ ${#inseguras[@]} -gt 0 ]; then
    echo ">> ERROR: cambia estos valores de plantilla en .env antes de desplegar: ${inseguras[*]}" >&2
    exit 1
  fi
}

cargar_env

case "$ACCION" in
  up)
    preparar_env
    cargar_env
    validar_env
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
    echo ">> Respaldo en backups/fidelizacion-${stamp}.sql"
    if docker compose -f "$COMPOSE_FILE" exec -T api sh -c 'cat "${CATALOGO_PATH:-/app/data/catalogo.json}"' > "backups/catalogo-${stamp}.json"; then
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
