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
        # Week info
        w = c.execute("SELECT * FROM week WHERE id=?", (week_id,)).fetchone()
        
        # Artifacts for this week
        arts = c.execute("SELECT * FROM artifact WHERE week_id=? ORDER BY created_at DESC", (week_id,)).fetchall()
        
        # Artifact counts by type
        art_counts = c.execute("""SELECT kind, COUNT(*) n FROM artifact 
                                  WHERE week_id=? GROUP BY kind""", (week_id,)).fetchall()
        
        # Time spent during this week (approximate by date range)
        week_sessions = []
        week_study_time = 0
        week_build_time = 0
        
        if w:
            week_sessions = c.execute("""SELECT * FROM session_log 
                                         WHERE date(started_at) BETWEEN ? AND ?
                                         ORDER BY started_at DESC""", 
                                     (w["start_date"], w["end_date"])).fetchall()
            
            # Calculate totals
            study_total = c.execute("""SELECT COALESCE(SUM(minutes), 0) as total 
                                       FROM session_log 
                                       WHERE date(started_at) BETWEEN ? AND ? 
                                       AND kind='study'""", 
                                   (w["start_date"], w["end_date"])).fetchone()["total"]
            
            build_total = c.execute("""SELECT COALESCE(SUM(minutes), 0) as total 
                                       FROM session_log 
                                       WHERE date(started_at) BETWEEN ? AND ? 
                                       AND kind='build'""", 
                                   (w["start_date"], w["end_date"])).fetchone()["total"]
            
            week_study_time = study_total
            week_build_time = build_total
            
        # Metrics for this week (match by week field in JSON)
        week_metrics = []
        if w:
            import json
            all_metrics = c.execute("SELECT * FROM artifact WHERE kind='metric' ORDER BY created_at DESC").fetchall()
            for metric in all_metrics:
                try:
                    meta = json.loads(metric["meta_json"]) if metric["meta_json"] else {}
                    if meta.get("week") == w["start_date"]:  # Match week start date
                        week_metrics.append({
                            **dict(metric),
                            "parsed_data": meta
                        })
                except:
                    pass
        
        # Startup info (if any)
        st = c.execute("SELECT * FROM startup WHERE week_id=?", (week_id,)).fetchone()
        
    return templates.TemplateResponse("week.html", {
        "request": request, 
        "week": w, 
        "arts": arts,
        "art_counts": art_counts,
        "week_sessions": week_sessions,
        "week_study_time": week_study_time,
        "week_build_time": week_build_time,
        "week_metrics": week_metrics,
        "startup": st
    })
