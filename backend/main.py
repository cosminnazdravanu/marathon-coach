# backend/main.py
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.routes.training_plan_routes import router as training_plan_router
from backend.routes.activity_routes import router as activity_router
from backend.db.session import init_models
import backend.config as config
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

# Initialize DB tables at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_models()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Routers
app.include_router(activity_router)
app.include_router(training_plan_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cookie-based sessions (no Redis)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
    same_site="lax",
    https_only=False,             # set True in prod behind HTTPS
    max_age=14 * 24 * 60 * 60,
)

# Static files
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)

@app.get("/")
def read_root():
    return {
        "message": "Marathon Coach FastAPI backend is running 🚀",
        "strava_client_id": bool(config.STRAVA_CLIENT_ID),
    }
