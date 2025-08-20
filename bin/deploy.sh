#!/usr/bin/env bash
set -euo pipefail
# Usage: /srv/personal/levels/bin/deploy.sh <RELEASE_NAME>

APP_DIR=/srv/personal/levels
VENV=$APP_DIR/venv
SHARED=$APP_DIR/shared
RELEASES=$APP_DIR/releases
REL="${1:?release name required}"
NEW="$RELEASES/$REL"

cd "$APP_DIR"

# venv bootstrap (once / idempotent)
[ -d "$VENV" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install --upgrade pip wheel

# install deps for this release
if [ -f "$NEW/requirements.txt" ]; then
  "$VENV/bin/pip" install -r "$NEW/requirements.txt"
elif [ -f "$NEW/pyproject.toml" ]; then
  (cd "$NEW" && "$VENV/bin/pip" install .)
fi

# link shared (.env, db, logs)
ln -sfn "$SHARED" "$NEW/shared"

# (optional) alembic
if [ -f "$NEW/alembic.ini" ] || [ -d "$NEW/alembic" ]; then
  (cd "$NEW" && "$VENV/bin/alembic" upgrade head || true)
fi

# flip symlink atomically and restart
ln -sfn "$NEW" "$APP_DIR/current"
sudo systemctl restart levels
echo "✅ Deployed $REL"
