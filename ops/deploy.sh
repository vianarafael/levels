#!/usr/bin/env bash
set -euo pipefail
# Usage: APP=levels SCOPE=personal ./ops/deploy.sh [--no-restart]
APP="${APP:-levels}"
SCOPE="${SCOPE:-personal}"              # personal|startups|anything
TARGET="${TARGET:-rafael}"               # ssh alias
REMOTE="/srv/${SCOPE}/${APP}/current"
SERVICE="${SERVICE:-$APP}"
NO_RESTART="${1:-}"

echo "🔄 Syncing -> $TARGET:$REMOTE"
rsync -avz --delete --delete-excluded \
  --exclude '.git' --exclude '.venv' --exclude '__pycache__' --exclude '.DS_Store' \
  ./ "$TARGET:$REMOTE/"

if [ "$NO_RESTART" = "--no-restart" ]; then
  echo "⏭️  Skipping restart"; exit 0
fi

echo "🚀 Restarting $SERVICE"
# use -t for interactive sudo; remove -t after adding sudoers rule
ssh -t "$TARGET" "sudo systemctl restart '$SERVICE' || true; systemctl status '$SERVICE' --no-pager -n 5 || true"
echo "✅ Deployed"
