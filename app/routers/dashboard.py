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
        # Current week and last week for deltas
        weeks = c.execute("SELECT * FROM week ORDER BY start_date DESC LIMIT 2").fetchall()
        current_week = weeks[0] if weeks else None
        last_week = weeks[1] if len(weeks) > 1 else None
        
        # This week totals
        this_week_hours = 0
        this_week_artifacts = 0
        if current_week:
            this_week_time = c.execute("""SELECT COALESCE(SUM(minutes), 0) as total 
                                          FROM session_log 
                                          WHERE date(started_at) BETWEEN ? AND ?""", 
                                      (current_week["start_date"], current_week["end_date"])).fetchone()["total"]
            this_week_hours = this_week_time / 60
            
            this_week_artifacts = c.execute("""SELECT COALESCE(COUNT(*), 0) as total 
                                               FROM artifact WHERE week_id = ?""", 
                                           (current_week["id"],)).fetchone()["total"]
        
        # Last week totals for delta
        last_week_hours = 0
        last_week_artifacts = 0
        if last_week:
            last_week_time = c.execute("""SELECT COALESCE(SUM(minutes), 0) as total 
                                          FROM session_log 
                                          WHERE date(started_at) BETWEEN ? AND ?""", 
                                      (last_week["start_date"], last_week["end_date"])).fetchone()["total"]
            last_week_hours = last_week_time / 60
            
            last_week_artifacts = c.execute("""SELECT COALESCE(COUNT(*), 0) as total 
                                               FROM artifact WHERE week_id = ?""", 
                                           (last_week["id"],)).fetchone()["total"]
        
        # Calculate deltas
        hours_delta = this_week_hours - last_week_hours
        artifacts_delta = this_week_artifacts - last_week_artifacts
        
        # Story points for current week
        this_week_planned_points = 0
        this_week_delivered_points = 0
        if current_week:
            this_week_planned_points = c.execute("""SELECT COALESCE(SUM(estimate_points), 0) as total 
                                                    FROM artifact WHERE kind = 'task' AND status = 'pending' AND week_id = ?""", 
                                                (current_week["id"],)).fetchone()["total"]
            this_week_delivered_points = c.execute("""SELECT COALESCE(SUM(estimate_points), 0) as total 
                                                      FROM artifact WHERE kind = 'task' AND status = 'done' AND week_id = ?""", 
                                                    (current_week["id"],)).fetchone()["total"]
        
        # Last week story points for delta
        last_week_planned_points = 0
        last_week_delivered_points = 0
        if last_week:
            last_week_planned_points = c.execute("""SELECT COALESCE(SUM(estimate_points), 0) as total 
                                                    FROM artifact WHERE kind = 'task' AND status = 'pending' AND week_id = ?""", 
                                                (last_week["id"],)).fetchone()["total"]
            last_week_delivered_points = c.execute("""SELECT COALESCE(SUM(estimate_points), 0) as total 
                                                      FROM artifact WHERE kind = 'task' AND status = 'done' AND week_id = ?""", 
                                                    (last_week["id"],)).fetchone()["total"]
        
        # Calculate deltas
        planned_points_delta = this_week_planned_points - last_week_planned_points
        delivered_points_delta = this_week_delivered_points - last_week_delivered_points
        
        # Output score (simple: artifacts + hours/10)
        output_score = this_week_artifacts + (this_week_hours / 10)
        last_output_score = last_week_artifacts + (last_week_hours / 10)
        score_delta = output_score - last_output_score
        
        # Latest 10 outputs (artifacts) - exclude metrics for now, show separately
        latest_outputs = c.execute("""SELECT * FROM artifact 
                                      WHERE kind != 'metric'
                                      ORDER BY created_at DESC LIMIT 10""").fetchall()
        
        # Latest metrics for dashboard KPIs - parse JSON here
        metrics_raw = c.execute("""SELECT * FROM artifact 
                                   WHERE kind = 'metric'
                                   ORDER BY created_at DESC LIMIT 5""").fetchall()
        latest_metrics = []
        for metric in metrics_raw:
            try:
                import json
                parsed_data = json.loads(metric["meta_json"]) if metric["meta_json"] else {}
                latest_metrics.append({
                    **dict(metric),
                    "parsed_data": parsed_data
                })
            except:
                latest_metrics.append(dict(metric))
        
        # Last 14 days minutes for sparkline
        daily_minutes = c.execute("""SELECT date(started_at) d, 
                                            COALESCE(SUM(minutes), 0) as total_min
                                     FROM session_log 
                                     GROUP BY d 
                                     ORDER BY d DESC LIMIT 14""").fetchall()
        
        # Reverse for chronological order in sparkline
        daily_minutes = list(reversed(daily_minutes))
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "this_week_hours": this_week_hours,
        "this_week_artifacts": this_week_artifacts,
        "this_week_planned_points": this_week_planned_points,
        "this_week_delivered_points": this_week_delivered_points,
        "output_score": output_score,
        "hours_delta": hours_delta,
        "artifacts_delta": artifacts_delta,
        "planned_points_delta": planned_points_delta,
        "delivered_points_delta": delivered_points_delta,
        "score_delta": score_delta,
        "latest_outputs": latest_outputs,
        "latest_metrics": latest_metrics,
        "daily_minutes": daily_minutes
    })
