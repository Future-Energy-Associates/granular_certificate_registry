#!/usr/bin/env bash
# Dump both databases to /srv/gcos/backups and keep seven days of dumps.
# The directory lives on the data volume, which is also snapshotted.
#
# Restore one dump into a running container, for example:
#   deploy/compose/dc.sh exec -T db_write sh -c \
#     'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' \
#     < /srv/gcos/backups/write-<stamp>.dump
set -euo pipefail
umask 077

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dir=/srv/gcos/backups
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$dir"

for name in read write; do
  tmp="${dir}/.${name}-${stamp}.tmp"
  # shellcheck disable=SC2016 # The variables expand inside the container.
  "${here}/dc.sh" exec -T "db_${name}" \
    sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$tmp"
  mv "$tmp" "${dir}/${name}-${stamp}.dump"
done

find "$dir" -name '*.dump' -mtime +7 -delete
