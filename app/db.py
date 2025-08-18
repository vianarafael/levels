
import os, sqlite3
from contextlib import contextmanager

DB_PATH = os.environ.get("LEVELS_DB", "./levels.db")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.executescript(open(os.path.join(os.path.dirname(__file__), "models.sql")).read())

@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
    finally:
        c.close()

