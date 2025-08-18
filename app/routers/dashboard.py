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
            counts = c.execute("""SELECT kind, COUNT(*) n FROM artifact
                                 WHERE week_id=? GROUP BY kind""", (week["id"],)).fetchall()
        sessions = c.execute("""SELECT date(started_at) d, sum(minutes) m FROM session_log
                                 GROUP BY d ORDER BY d DESC LIMIT 14""").fetchall()
    return templates.TemplateResponse("dashboard.html", {"request": request, "week": week, "counts": counts, "sessions": sessions})
