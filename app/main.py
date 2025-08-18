import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .db import init_db
from .routers import dashboard, health, weeks

app = FastAPI(title="Levels")

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

app.include_router(dashboard.router)
app.include_router(health.router)
app.include_router(weeks.router)

@app.on_event("startup")
def _startup():
    init_db()


