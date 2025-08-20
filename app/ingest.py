import os, json, datetime as dt, subprocess, re
from pathlib import Path
from .db import conn

INBOX = Path(os.environ.get("LEVELS_INBOX", "/srv/personal/levels/inbox"))
OUTBOX = Path(os.environ.get("LEVELS_OUTBOX", "/srv/personal/levels/outbox"))
MEDIA = Path(os.environ.get("LEVELS_MEDIA", "/srv/personal/levels/media"))

def mark(c, rel, status, msg=""):
    c.execute("""
      INSERT INTO ingest_status(rel_path, first_seen, status)
      VALUES(?,?,?)
      ON CONFLICT(rel_path) DO UPDATE SET last_ingested=?, status=?, message=?""",
      (rel, dt.datetime.now().isoformat(), "pending",
       dt.datetime.now().isoformat(), status, msg))

def probe_duration_mp4(p: Path)->float:
    out = subprocess.check_output([
      "ffprobe","-v","error","-show_entries","format=duration","-of","default=nokey=1:noprint_wrappers=1", str(p)
    ])
    return float(out.decode().strip())

def get_current_week_id(c):
    """Get or create current week ID (Monday to Sunday)"""
    today = dt.date.today()
    start = today - dt.timedelta(days=today.weekday())
    end = start + dt.timedelta(days=6)
    
    # Try to get existing week
    week = c.execute("SELECT id FROM week WHERE start_date = ?", (start.isoformat(),)).fetchone()
    if week:
        return week[0]
    
    # Create new week if it doesn't exist
    cursor = c.execute("INSERT INTO week(start_date, end_date) VALUES(?, ?)", 
                       (start.isoformat(), end.isoformat()))
    return cursor.lastrowid

def parse_markdown_checklist(content: str, week_id: int):
    """Parse markdown checklist and return list of artifact tuples"""
    # Pattern: ^- \[( |x)\] \((\d+)\) (.+)$
    pattern = r'^- \[( |x)\] \((\d+)\) (.+)$'
    artifacts = []
    
    for line in content.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            status_char, points_str, title = match.groups()
            status = "done" if status_char == "x" else "pending" 
            estimate_points = int(points_str)
            artifacts.append(("task", title, None, None, {}, estimate_points, status, week_id))
    
    return artifacts

def process():
    MEDIA.mkdir(parents=True, exist_ok=True)
    INBOX.mkdir(parents=True, exist_ok=True)
    OUTBOX.mkdir(parents=True, exist_ok=True)
    
    with conn() as c:
        current_week_id = get_current_week_id(c)
        
        # Process OUTBOX first (for plans)
        for p in OUTBOX.rglob("*"):
            if not p.is_file(): continue
            rel = str(p.relative_to(OUTBOX))
            try:
                # Handle markdown plans in build/plans/
                if "build/plans/" in rel and p.suffix == ".md":
                    content = p.read_text(encoding="utf-8")
                    artifacts = parse_markdown_checklist(content, current_week_id)
                    
                    for kind, title, path, text, meta, estimate_points, status, week_id in artifacts:
                        c.execute("""INSERT INTO artifact(kind,title,path,text_content,meta_json,estimate_points,status,week_id,created_at)
                                     VALUES(?,?,?,?,?,?,?,?,datetime('now'))""",
                                  (kind, title, path, text, json.dumps(meta), estimate_points, status, week_id))
                    
                    mark(c, rel, "ok", f"Parsed {len(artifacts)} tasks")
                    # Move processed file to avoid reprocessing
                    p.unlink()
                else:
                    continue
            except Exception as e:
                mark(c, rel, "error", str(e))
        
        # Process INBOX (existing logic)
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
                elif rel.startswith("metrics/") and p.suffix==".json":
                    path=str(p); meta=json.loads(p.read_text()); kind="metric"
                    # Extract week from filename or JSON for title
                    if "week" in meta:
                        title = f"{meta.get('app', 'app')}-{meta['week']}"
                    else:
                        title = p.stem
                else:
                    continue

                c.execute("""INSERT INTO artifact(kind,title,path,text_content,meta_json,week_id,created_at)
                             VALUES(?,?,?,?,?,?,datetime('now'))""",
                          (kind,title,path,text,json.dumps(meta),current_week_id))
                mark(c, rel, "ok", "")
            except Exception as e:
                mark(c, rel, "error", str(e))

if __name__ == "__main__":
    process()
