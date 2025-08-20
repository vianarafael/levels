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
  estimate_points INTEGER,
  status TEXT DEFAULT 'pending',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session_log (
  id INTEGER PRIMARY KEY,
  started_at TEXT, ended_at TEXT, minutes INTEGER,
  kind TEXT,    -- build|study
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
