# backend/main.py
import os
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from .db.session import init_models
from contextlib import asynccontextmanager

import backend.config as config
from backend.routes.auth_routes import router as auth_router
from backend.routes.activity_routes import router as activity_router
from backend.routes.training_plan_routes import router as training_plan_router

@asynccontextmanager
async def lifespan(app):
    init_models()   # <- this creates missing tables
    yield

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def enforce_localhost(request: Request, call_next):
    host = request.headers.get("host", "")
    if host.startswith("127.0.0.1"):
        # preserve path/query while redirecting
        new_url = str(request.url).replace("127.0.0.1", "localhost")
        return RedirectResponse(url=new_url, status_code=307)  # 307 keeps method + body
    return await call_next(request)

# Prometheus metrics
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Routers
app.include_router(auth_router)
app.include_router(activity_router)
app.include_router(training_plan_router)

# CORS (adjust as needed for your dev/prod hosts)
app.add_middleware(
    CORSMiddleware,
    # Accept only http://localhost:<any port>
    allow_origin_regex=r"^http://localhost:\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Cookie-based sessions (set https_only=True in production over HTTPS)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    same_site="lax",
    https_only=False,  # True in prod
    max_age=14 * 24 * 60 * 60,
    domain=os.getenv("SESSION_COOKIE_DOMAIN"),
)

# Static files
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

@app.get("/status")
def read_status():
    return {
        "message": "Marathon Coach FastAPI backend is running 🚀",
        "strava_client_id": bool(config.STRAVA_CLIENT_ID),
    }

