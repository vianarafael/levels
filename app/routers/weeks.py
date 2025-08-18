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
