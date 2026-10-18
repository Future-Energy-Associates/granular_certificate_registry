#!/usr/bin/env bash
# Roll the host to one commit. Runs as root on the instance, normally through
# AWS Systems Manager from the publish workflow:
#
#   cd /opt/gcos
#   git fetch --depth 1 origin <sha> && git checkout --detach FETCH_HEAD
#   deploy/compose/deploy.sh <sha>
#
# The images tagged <sha> must already be in the registry.
#
# Environment:
#   RUN_MIGRATIONS=0   skip `alembic upgrade head`. Use it on the first deploy
#                      when you are about to restore dumps into the databases.
set -euo pipefail
umask 077

readonly INSTANCE_ENV=/etc/gcos/instance.env
readonly APP_ENV=/etc/gcos/app.env
readonly RELEASE_ENV=/etc/gcos/release.env

sha="${1:-}"
if [[ ! "$sha" =~ ^[0-9a-f]{40}$ ]]; then
  echo "usage: deploy.sh <40-character commit sha>" >&2
  exit 2
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dc="${here}/dc.sh"

set -a
# shellcheck disable=SC1090
source "$INSTANCE_ENV"
set +a

echo "Fetching application settings"
aws secretsmanager get-secret-value \
  --region "$AWS_REGION" \
  --secret-id "$SECRET_ID" \
  --query SecretString \
  --output text > "${APP_ENV}.tmp"
chmod 600 "${APP_ENV}.tmp"
mv "${APP_ENV}.tmp" "$APP_ENV"

cat > "${RELEASE_ENV}.tmp" <<EOF
API_IMAGE=${ECR_REGISTRY}/${API_REPOSITORY}:${sha}
FRONTEND_IMAGE=${ECR_REGISTRY}/${FRONTEND_REPOSITORY}:${sha}
EOF
chmod 600 "${RELEASE_ENV}.tmp"
mv "${RELEASE_ENV}.tmp" "$RELEASE_ENV"

echo "Pulling images"
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY" >/dev/null
"$dc" pull

echo "Starting data services"
"$dc" up -d --wait db_read db_write eventstore

if [[ "${RUN_MIGRATIONS:-1}" != "0" ]]; then
  echo "Running migrations"
  "$dc" run --rm --no-deps -T gc_registry alembic upgrade head
fi

echo "Starting application"
"$dc" up -d --remove-orphans

echo "Installing timers"
install -m 644 "${here}"/systemd/*.service "${here}"/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now gcos-backup.timer

echo "Waiting for the API"
for _ in $(seq 1 24); do
  if curl -fsS "http://${PRIVATE_BIND_IP}:8080/" >/dev/null 2>&1; then
    docker image prune -f >/dev/null
    echo "Deployed ${sha}"
    exit 0
  fi
  sleep 5
done

echo "The API did not answer within two minutes" >&2
"$dc" ps >&2
exit 1
