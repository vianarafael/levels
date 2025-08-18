#!/usr/bin/env bash
set -euo pipefail
mkdir -p /srv/personal/levels/{inbox,media}
mkdir -p /var/log/levels
cp .env.example .env || true
echo "Bootstrap done. Edit /srv/personal/levels/.env and run: make install && make dev"
