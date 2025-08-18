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
