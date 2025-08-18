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
