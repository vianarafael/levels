#!/usr/bin/env python3
"""
Manually add session logs for testing the RPG system.
Usage: python3 scripts/add_session.py <minutes> <kind> <skill> [notes]
"""
import os, sqlite3, sys
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.db import init_db, DB_PATH

def add_session(minutes: int, kind: str, notes: str = ""):
    init_db()
    
    # Create fake session log entry
    now = datetime.now()
    started_at = (now - timedelta(minutes=minutes)).isoformat()
    ended_at = now.isoformat()
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            INSERT INTO session_log (started_at, ended_at, minutes, kind, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (started_at, ended_at, minutes, kind, notes))
        
        session_id = cursor.lastrowid
        conn.commit()
        
        print(f"✅ Added {minutes}min {kind} session (ID: {session_id})")
        return session_id

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/add_session.py <minutes> <kind> [notes]")
        print("Example: python3 scripts/add_session.py 30 study 'Learning databases'")
        sys.exit(1)
    
    minutes = int(sys.argv[1])
    kind = sys.argv[2]  # build or study
    notes = sys.argv[3] if len(sys.argv) > 3 else ""
    
    add_session(minutes, kind, notes)
