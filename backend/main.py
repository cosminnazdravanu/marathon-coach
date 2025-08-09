# backend/main.py
import os
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

import backend.config as config
from backend.routes.auth_routes import router as auth_router
from backend.routes.activity_routes import router as activity_router
from backend.routes.training_plan_routes import router as training_plan_router

app = FastAPI()

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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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

