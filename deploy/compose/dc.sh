#!/usr/bin/env bash
# Run `docker compose` against the production stack with the right project
# name, compose file, and env files.
#
#   deploy/compose/dc.sh ps
#   deploy/compose/dc.sh logs -f gc_registry
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
env_args=(--env-file /etc/gcos/instance.env)
if [[ -f /etc/gcos/release.env ]]; then
  env_args+=(--env-file /etc/gcos/release.env)
fi

exec docker compose \
  --project-name registry \
  -f "${here}/compose.prod.yml" \
  "${env_args[@]}" \
  "$@"
