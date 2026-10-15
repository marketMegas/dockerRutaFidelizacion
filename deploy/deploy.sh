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

case "$ACCION" in
  up)
    preparar_env
    echo ">> Construyendo y levantando contenedores..."
    docker compose -f "$COMPOSE_FILE" up -d --build
    echo
    docker compose -f "$COMPOSE_FILE" ps
    echo
    sleep 3
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
    docker compose -f "$COMPOSE_FILE" up -d --build
    docker compose -f "$COMPOSE_FILE" ps
    ;;
  logs)
    docker compose -f "$COMPOSE_FILE" logs -f "${2:-}"
    ;;
  backup)
    mkdir -p backups
    stamp="$(date +%Y%m%d-%H%M%S)"
    docker compose -f "$COMPOSE_FILE" exec -T db pg_dump -U "${POSTGRES_USER:-fidelizacion}" "${POSTGRES_DB:-fidelizacion}" > "backups/fidelizacion-${stamp}.sql"
    echo ">> Respaldo en backups/fidelizacion-${stamp}.sql"
    ;;
  *)
    echo "Uso: deploy.sh [up|down|update|logs|backup]"
    exit 1
    ;;
esac
