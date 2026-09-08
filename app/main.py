from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import settings
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)
app = FastAPI(title="PulsePath Wearable Health API", version="1.0.0", description="IoT wearable vitals ingestion, analytics, alerts and a safe health assistant.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env}


@app.get("/ready")
def ready():
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}


web_dir = Path(__file__).resolve().parent.parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="web")
