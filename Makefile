.PHONY: dev install upload initdb

  dev:
	uvicorn app.main:app --reload --port 8080

  install:
	python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	mkdir -p /srv/levels/{inbox,media}
	mkdir -p /var/log/levels
	cp .env.example .env || true

  initdb:
	python3 scripts/seed.py

  upload:
	bash local/bin/rsync-upload
