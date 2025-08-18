#!/usr/bin/env python3
import os, stat, textwrap, pathlib

ROOT = pathlib.Path(__file__).resolve().parent

def write(path, content):
  p = ROOT / path
  p.parent.mkdir(parents=True, exist_ok=True)
  if p.exists():
    print(f"skip (exists): {path}")
    return
  p.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
  print(f"created: {path}")

def make_exec(path):
  p = ROOT / path
  p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def main():
  # --- base files
  write("requirements.txt", """
  fastapi==0.112.2
  uvicorn[standard]==0.30.6
  jinja2==3.1.4
  python-multipart==0.0.9
  pydantic==2.8.2
  sqlite-utils==3.37
  python-dotenv==1.0.1
  """)
  write(".env.example", """
  LEVELS_DB=/srv/levels/levels.db
  LEVELS_INBOX=/srv/levels/inbox
  LEVELS_MEDIA=/srv/levels/media
  LEVELS_LOG=/var/log/levels
  SECRET_KEY=change-me
  """)
  write("Makefile", """
  .PHONY: dev install upload initdb

  dev:
\tuvicorn app.main:app --reload --port 8080

  install:
\tpython3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
\tmkdir -p /srv/levels/{inbox,media}
\tmkdir -p /var/log/levels
\tcp .env.example .env || true

  initdb:
\tpython3 scripts/seed.py

  upload:
\tbash local/bin/rsync-upload
  """)

  # --- app
  write("app/models.sql", """
  PRAGMA journal_mode=WAL;

  CREATE TABLE IF NOT EXISTS week (
    id INTEGER PRIMARY KEY,
    start_date TEXT UNIQUE,
    end_date   TEXT,
    notes TEXT
  );

  CREATE TABLE IF NOT EXISTS startup (
    id INTEGER PRIMARY KEY,
    week_id INTEGER REFERENCES week(id) ON DELETE CASCADE,
    title TEXT, repo_url TEXT, deployed_url TEXT,
    description TEXT, status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS artifact (
    id INTEGER PRIMARY KEY,
    week_id INTEGER REFERENCES week(id) ON DELETE SET NULL,
    startup_id INTEGER REFERENCES startup(id) ON DELETE SET NULL,
    kind TEXT, title TEXT, path TEXT,
    text_content TEXT, meta_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS session_log (
    id INTEGER PRIMARY KEY,
    started_at TEXT, ended_at TEXT, minutes INTEGER,
    kind TEXT,    -- build|study
    skill TEXT,   -- fastapi|vectordb|etl|indiehacker|neovim|vibe
    notes TEXT
  );

  CREATE TABLE IF NOT EXISTS ingest_status (
    id INTEGER PRIMARY KEY,
    rel_path TEXT UNIQUE,
    first_seen TEXT, last_ingested TEXT,
    status TEXT, message TEXT
  );

  CREATE INDEX IF NOT EXISTS idx_artifact_week ON artifact(week_id);
  CREATE INDEX IF NOT EXISTS idx_artifact_kind ON artifact(kind);
  CREATE INDEX IF NOT EXISTS idx_session_kind ON session_log(kind);
  """)
  write("app/db.py", """
  import os, sqlite3
  from contextlib import contextmanager

  DB_PATH = os.environ.get("LEVELS_DB", "./levels.db")

  def init_db():
      with sqlite3.connect(DB_PATH) as c:
          c.executescript(open(os.path.join(os.path.dirname(__file__), "models.sql")).read())

  @contextmanager
  def conn():
      c = sqlite3.connect(DB_PATH)
      c.row_factory = sqlite3.Row
      try:
          yield c
      finally:
          c.close()
  """)
  write("app/utils.py", " # (optional helpers later)\n")
  write("app/main.py", """
  import os
  from fastapi import FastAPI, Request
  from fastapi.staticfiles import StaticFiles
  from fastapi.templating import Jinja2Templates
  from .db import init_db
  from .routers import dashboard, health, weeks

  app = FastAPI(title="Levels")

  BASE_DIR = os.path.dirname(__file__)
  templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
  app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

  app.include_router(dashboard.router)
  app.include_router(health.router)
  app.include_router(weeks.router)

  @app.on_event("startup")
  def _startup():
      init_db()
  """)
  write("app/routers/dashboard.py", """
  import os
  from fastapi import APIRouter, Request
  from fastapi.responses import HTMLResponse
  from fastapi.templating import Jinja2Templates
  from ..db import conn

  router = APIRouter()
  templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

  @router.get("/", response_class=HTMLResponse)
  def home(request: Request):
      with conn() as c:
          week = c.execute("SELECT * FROM week ORDER BY start_date DESC LIMIT 1").fetchone()
          counts = []
          if week:
              counts = c.execute(\"\"\"SELECT kind, COUNT(*) n FROM artifact
                                   WHERE week_id=? GROUP BY kind\"\"\", (week["id"],)).fetchall()
          sessions = c.execute(\"\"\"SELECT date(started_at) d, sum(minutes) m FROM session_log
                                   GROUP BY d ORDER BY d DESC LIMIT 14\"\"\").fetchall()
      return templates.TemplateResponse("dashboard.html", {"request": request, "week": week, "counts": counts, "sessions": sessions})
  """)
  write("app/routers/health.py", """
  import os
  from fastapi import APIRouter, Request
  from fastapi.responses import HTMLResponse
  from fastapi.templating import Jinja2Templates
  from ..db import conn

  router = APIRouter(prefix="/health")
  templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

  @router.get("/", response_class=HTMLResponse)
  def health(request: Request):
      with conn() as c:
          rows = c.execute("SELECT * FROM ingest_status ORDER BY COALESCE(last_ingested, first_seen) DESC LIMIT 100").fetchall()
          pending = c.execute("SELECT COUNT(*) n FROM ingest_status WHERE status='pending'").fetchone()["n"] if rows else 0
          errors  = c.execute("SELECT COUNT(*) n FROM ingest_status WHERE status='error'").fetchone()["n"] if rows else 0
      return templates.TemplateResponse("health.html", {"request": request, "rows": rows, "pending": pending, "errors": errors})
  """)
  write("app/routers/weeks.py", """
  import os
  from fastapi import APIRouter, Request
  from fastapi.responses import HTMLResponse
  from fastapi.templating import Jinja2Templates
  from ..db import conn

  router = APIRouter(prefix="/week")
  templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))

  @router.get("/{week_id}", response_class=HTMLResponse)
  def week_view(week_id: int, request: Request):
      with conn() as c:
          w = c.execute("SELECT * FROM week WHERE id=?", (week_id,)).fetchone()
          arts = c.execute("SELECT * FROM artifact WHERE week_id=? ORDER BY created_at DESC", (week_id,)).fetchall()
          st = c.execute("SELECT * FROM startup WHERE week_id=?", (week_id,)).fetchone()
      return templates.TemplateResponse("week.html", {"request": request, "week": w, "arts": arts, "startup": st})
  """)
  write("app/templates/base.html", """
  <!doctype html><html><head>
  <meta charset="utf-8"><title>Levels</title>
  <script src="/static/htmx.min.js"></script>
  <style>
  body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem;}
  header{display:flex;gap:1rem;align-items:center;margin-bottom:1rem;}
  nav a{margin-right:1rem;} table{width:100%;border-collapse:collapse;}
  th,td{border-bottom:1px solid #eee;padding:.5rem;}
  .kpi{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin:1rem 0;}
  .card{border:1px solid #eee;border-radius:12px;padding:1rem;}
  </style></head><body>
  <header><h1>Levels</h1><nav><a href="/">Dashboard</a><a href="/health/">Health</a></nav></header>
  {% block body %}{% endblock %}
  </body></html>
  """)
  write("app/templates/dashboard.html", """
  {% extends "base.html" %}{% block body %}
  <div class="kpi">
    <div class="card"><h3>This Week</h3>
      {% if week %}<p>{{week.start_date}} → {{week.end_date}}</p>{% else %}<p>No week created yet.</p>{% endif %}
    </div>
    <div class="card"><h3>Artifacts (by type)</h3><ul>
      {% for r in counts %}<li>{{r.kind}}: {{r.n}}</li>{% endfor %}
    </ul></div>
    <div class="card"><h3>Study (last 14 days)</h3><ul>
      {% for s in sessions %}<li>{{s["d"]}} — {{s["m"]}} min</li>{% endfor %}
    </ul></div>
  </div>
  {% endblock %}
  """)
  write("app/templates/health.html", """
  {% extends "base.html" %}{% block body %}
  <div class="card"><h3>Ingest Health</h3>
    <p>Pending: {{pending}} · Errors: {{errors}}</p>
    <table><tr><th>Path</th><th>Status</th><th>First Seen</th><th>Last Ingested</th><th>Message</th></tr>
    {% for r in rows %}<tr>
      <td>{{r["rel_path"]}}</td><td>{{r["status"]}}</td><td>{{r["first_seen"]}}</td><td>{{r["last_ingested"]}}</td><td>{{r["message"]}}</td>
    </tr>{% endfor %}</table>
  </div>{% endblock %}
  """)
  write("app/templates/week.html", """
  {% extends "base.html" %}{% block body %}
  <h2>Week {{week.id}} — {{week.start_date}} → {{week.end_date}}</h2>
  {% if startup %}<div class="card"><h3>Startup of the Week</h3>
  <p><strong>{{startup.title}}</strong></p><p>Repo: {{startup.repo_url}} · Deployed: {{startup.deployed_url}}</p><p>{{startup.description}}</p></div>{% endif %}
  <div class="card"><h3>Artifacts</h3>
    <table><tr><th>Kind</th><th>Title</th><th>Path</th><th>Created</th></tr>
    {% for a in arts %}<tr><td>{{a.kind}}</td><td>{{a.title}}</td><td>{{a.path}}</td><td>{{a.created_at}}</td></tr>{% endfor %}
    </table></div>
  {% endblock %}
  """)
  write("app/static/htmx.min.js", "// add htmx dist here when you want\n")
  write("app/ingest.py", """
  import os, json, datetime as dt, subprocess
  from pathlib import Path
  from .db import conn

  INBOX = Path(os.environ.get("LEVELS_INBOX", "/srv/levels/inbox"))
  MEDIA = Path(os.environ.get("LEVELS_MEDIA", "/srv/levels/media"))

  def mark(c, rel, status, msg=""):
      c.execute(\"\"\"
        INSERT INTO ingest_status(rel_path, first_seen, status)
        VALUES(?,?,?)
        ON CONFLICT(rel_path) DO UPDATE SET last_ingested=?, status=?, message=?\"\"",
        (rel, dt.datetime.now().isoformat(), "pending",
         dt.datetime.now().isoformat(), status, msg))

  def probe_duration_mp4(p: Path)->float:
      out = subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration","-of","default=nokey=1:noprint_wrappers=1", str(p)
      ])
      return float(out.decode().strip())

  def process():
      MEDIA.mkdir(parents=True, exist_ok=True)
      INBOX.mkdir(parents=True, exist_ok=True)
      with conn() as c:
          for p in INBOX.rglob("*"):
              if not p.is_file(): continue
              rel = str(p.relative_to(INBOX))
              try:
                  kind, title, path, text, meta = None, p.stem, "", None, {}
                  if "/build/recordings/" in rel and p.suffix==".mp4":
                      dest = MEDIA/"recordings"/p.name; dest.parent.mkdir(parents=True, exist_ok=True)
                      p.replace(dest); path=str(dest); meta={"duration":probe_duration_mp4(Path(path))}
                      kind="recording"
                  elif "/build/notes/" in rel and p.suffix in (".md",".txt"):
                      path=str(p); text=p.read_text(encoding="utf-8"); kind="note"
                  elif "/build/conversations/" in rel and p.suffix in (".md",".txt"):
                      path=str(p); text=p.read_text(encoding="utf-8"); kind="conversation"
                  elif "/build/repos/" in rel and p.suffix in (".txt",):
                      path=str(p); text=p.read_text().strip(); kind="repo"
                  elif "/study/books/" in rel and p.suffix.lower() in (".pdf",".epub",".mobi"):
                      dest = MEDIA/"books"/p.name; dest.parent.mkdir(parents=True, exist_ok=True)
                      p.replace(dest); path=str(dest); kind="book"
                  elif "/study/notes/" in rel and p.suffix in (".md",".txt",".csv"):
                      path=str(p); text=p.read_text(encoding="utf-8", errors="ignore"); kind="study_note"
                  elif "/study/challenges/" in rel and p.name=="codewars.json":
                      path=str(p); meta=json.loads(p.read_text()); kind="challenge"
                  elif "/study/challenges/" in rel and p.name=="overthewire.md":
                      path=str(p); text=p.read_text(); kind="challenge"
                  else:
                      continue

                  c.execute(\"\"\"INSERT INTO artifact(kind,title,path,text_content,meta_json,created_at)
                               VALUES(?,?,?,?,?,datetime('now'))\"\"",
                            (kind,title,path,text,json.dumps(meta)))
                  mark(c, rel, "ok", "")
              except Exception as e:
                  mark(c, rel, "error", str(e))

  if __name__ == "__main__":
      process()
  """)

  # --- server configs
  write("server/gunicorn.conf.py", """
  bind = "0.0.0.0:8080"
  workers = 2
  worker_class = "uvicorn.workers.UvicornWorker"
  timeout = 120
  """)
  write("server/nginx.conf.example", """
  server {
    listen 80;
    server_name levels.example.com;
    location / {
      proxy_pass http://127.0.0.1:8080;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }
  }
  """)
  write("server/systemd/levels.service", """
  [Unit]
  Description=Levels FastAPI
  After=network.target

  [Service]
  User=www-data
  WorkingDirectory=/srv/levels
  EnvironmentFile=/srv/levels/.env
  ExecStart=/usr/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
  Restart=always

  [Install]
  WantedBy=multi-user.target
  """)
  write("server/systemd/levels-ingest.service", """
  [Unit]
  Description=Levels Ingest Job

  [Service]
  Type=oneshot
  WorkingDirectory=/srv/levels
  EnvironmentFile=/srv/levels/.env
  ExecStart=/usr/bin/python3 /srv/levels/app/ingest.py
  """)
  write("server/systemd/levels-ingest.timer", """
  [Unit]
  Description=Run Levels Ingest every 10 minutes

  [Timer]
  OnBootSec=2min
  OnUnitActiveSec=10min
  Unit=levels-ingest.service

  [Install]
  WantedBy=timers.target
  """)

  # --- scripts
  write("scripts/bootstrap.sh", """
  #!/usr/bin/env bash
  set -euo pipefail
  mkdir -p /srv/levels/{inbox,media}
  mkdir -p /var/log/levels
  cp .env.example .env || true
  echo "Bootstrap done. Edit /srv/levels/.env and run: make install && make dev"
  """)
  make_exec("scripts/bootstrap.sh")

  write("scripts/seed.py", """
  import os, sqlite3
  from app.db import init_db, DB_PATH
  init_db()
  with sqlite3.connect(DB_PATH) as c:
      # create current week if missing (Mon..Sun)
      import datetime as dt
      today = dt.date.today()
      start = today - dt.timedelta(days=today.weekday())
      end = start + dt.timedelta(days=6)
      c.execute("INSERT OR IGNORE INTO week(start_date,end_date) VALUES(?,?)",
                (start.isoformat(), end.isoformat()))
  print("DB initialized and current week ensured.")
  """)
  write("scripts/codewars_sync.py", """
  # stub: later use Codewars API to fetch solved katas and write to inbox/study/challenges/codewars.json
  if __name__ == "__main__":
      print("TODO: implement Codewars sync")
  """)
  write("scripts/crontab.example", """
  # Ingest inbox every 10 minutes (or change to daily)
  */10 * * * * /usr/bin/python3 /srv/levels/app/ingest.py >> /var/log/levels/ingest.log 2>&1
  """)

  # --- local toolkit
  write("local/config/paths.env", """
  export LEVELS_HOME="$HOME/levels"
  export OUTBOX="$LEVELS_HOME/outbox"
  export LOGDIR="$LEVELS_HOME/.levels-uploader"
  """)
  write("local/config/server.env", """
  export LEVELS_SSH="user@your-server"
  export REMOTE_INBOX="/srv/levels/inbox"
  """)
  write("local/bin/rsync-upload", """
  #!/usr/bin/env bash
  set -euo pipefail
  source "$(dirname "$0")/../config/paths.env"
  source "$(dirname "$0")/../config/server.env"
  mkdir -p "$LOGDIR"
  rsync -azP --delete "$OUTBOX/" "$LEVELS_SSH:$REMOTE_INBOX/" >> "$LOGDIR/upload.log" 2>&1
  """)
  write("local/bin/ship", """
  #!/usr/bin/env bash
  set -euo pipefail
  source "$(dirname "$0")/../config/paths.env"
  mkdir -p "$OUTBOX/study/notes" "$OUTBOX/build/notes"
  STATE="$LEVELS_HOME/.ship.state"
  case "${1:-help}" in
    start) echo "$(date -Iseconds),$2,${3:-}" > "$STATE"; echo "started $2 ${3:-}";;
    stop)
      if [ ! -f "$STATE" ]; then echo "no active session"; exit 1; fi
      IFS=',' read -r START KIND SKILL < "$STATE"
      END=$(date -Iseconds); rm -f "$STATE"
      echo "$START,$END,$KIND,$SKILL" >> "$OUTBOX/study/notes/sessions.csv"; echo "stopped";;
    note) shift; f="$OUTBOX/build/notes/$(date +%F).md"; echo "- $(date -Iseconds) $*" >> "$f"; echo "noted";;
    book) shift; f="$OUTBOX/study/notes/books.md"; echo "- $(date -Iseconds) $*" >> "$f"; echo "logged book";;
    *) echo "usage: ship start <build|study> [skill]; ship stop; ship note \"...\"; ship book \"...\"";;
  esac
  """)
  write("local/bin/nvim-wrap", """
  #!/usr/bin/env bash
  set -euo pipefail
  source "$(dirname "$0")/../config/paths.env"
  mkdir -p "$OUTBOX/study/notes"
  LOG="$OUTBOX/study/notes/nvim-time.csv"
  START=$(date -Iseconds)
  nvim "$@"
  END=$(date -Iseconds)
  echo "$START,$END,$PWD" >> "$LOG"
  """)
  for f in ["local/bin/rsync-upload","local/bin/ship","local/bin/nvim-wrap"]:
      make_exec(f)

  write("local/README.md", """
  # levels-local
  - Drop files into `~/levels/outbox/...`
  - `local/bin/rsync-upload` pushes to the server inbox.
  - `local/bin/ship` logs sessions/notes quickly.
  - `local/bin/nvim-wrap` logs Neovim usage minutes.
  Configure paths in `local/config/*.env`.
  """)

  print("\\nDone. Next: `python3 scripts/seed.py` then `uvicorn app.main:app --reload`")

if __name__ == "__main__":
  main()

