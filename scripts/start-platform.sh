#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

command -v docker >/dev/null 2>&1 || { echo 'Docker is required.' >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo 'Docker daemon is not running.' >&2; exit 1; }

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo 'Created .env; set POSTGRES_PASSWORD and MINIO_ROOT_PASSWORD before continuing.'
  exit 1
fi

if [[ ! -f services/yuxi/.env ]]; then
  cp services/yuxi/.env.template services/yuxi/.env
fi

secret() { (umask 077; openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n'); }
ensure_env() {
  local key="$1" value="$2"
  if ! grep -qE "^${key}=.+" services/yuxi/.env; then
    printf '\n%s=%s\n' "$key" "$value" >> services/yuxi/.env
  fi
}
ensure_env JWT_SECRET_KEY "$(secret)"
ensure_env API_KEY_DERIVATION_SECRET "$(secret)"
ensure_env SANDBOX_PROVISIONER_TOKEN "$(secret)"
ensure_env YUXI_INSTANCE_ID "instance-$(openssl rand -hex 8)"

docker compose --project-name geochat-runtime --project-directory services/yuxi up -d --build
docker compose --project-name deep-geology -f infra/compose/docker-compose.yml up -d --build
echo 'Platform started at http://localhost:8080/'
