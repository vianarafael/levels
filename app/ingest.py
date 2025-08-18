import os, json, datetime as dt, subprocess
from pathlib import Path
from .db import conn

INBOX = Path(os.environ.get("LEVELS_INBOX", "/srv/personal/levels/inbox"))
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

                c.execute("""INSERT INTO artifact(kind,title,path,text_content,meta_json,created_at)
                             VALUES(?,?,?,?,?,datetime('now'))""",
                          (kind,title,path,text,json.dumps(meta)))
                mark(c, rel, "ok", "")
            except Exception as e:
                mark(c, rel, "error", str(e))

if __name__ == "__main__":
    process()
