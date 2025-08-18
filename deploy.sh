cat >deploy.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
TARGET=rafael
REMOTE=/srv/personal/levels/current
SERVICE=levels

echo "🔄 Syncing..."
rsync -az --delete \
  --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
  ./ $TARGET:$REMOTE/

echo "🚀 Restarting..."
ssh $TARGET "sudo systemctl restart $SERVICE"

echo "✅ Deployed"
SH
chmod +x deploy.sh
