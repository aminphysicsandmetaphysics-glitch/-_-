from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.db.migrations import ensure_runtime_schema
from app.db.session import Base, engine
from app.models import entities

cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app = FastAPI(
    title="Iran Residential Energy Audit API",
    description="Level 1 and Level 2 energy audit platform aligned with مبحث ۱۹ for Iranian residential buildings.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials="*" not in cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Iran Residential Energy Audit API",
        "docs": "/docs",
        "health": "/health",
        "api_base": "/api/v1",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
def create_database_schema():
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema(engine)
