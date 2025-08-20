#!/usr/bin/env bash
set -euo pipefail
# Usage: APP=levels SCOPE=personal TARGET=rafael ./ops/deploy.sh

APP="${APP:-levels}"
SCOPE="${SCOPE:-personal}"        # personal|startups|...
TARGET="${TARGET:-rafael}"         # ssh alias in ~/.ssh/config
BASE="/srv/${SCOPE}/${APP}"
REL="$(git rev-parse --short HEAD)-$(date +%Y%m%d%H%M%S)"

echo "📤 Uploading release $REL -> $TARGET:$BASE/releases/$REL/"
rsync -az --delete \
  --exclude '.git' --exclude '.venv' --exclude '__pycache__' --exclude '.DS_Store' \
  ./ "$TARGET:$BASE/releases/$REL/"

echo "🚀 Activating release on server…"
ssh "$TARGET" "$BASE/bin/deploy.sh $REL"

echo "✅ Done"
