"""
NexGenIQ backend - FastAPI application entry point.

Wires together the API routers, configures CORS for the React frontend,
initialises the database, and exposes a health check. Run locally with:

    uvicorn app.main:app --reload

Interactive API documentation is then available at /docs.

Reference: NexGenIQ Phase 3 Part 3C.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    import_routes,
    index_routes,
    library_routes,
    sim_routes,
)
from app.core.config import get_settings
from app.core.database import init_db

_settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create database tables on startup."""
    init_db()
    yield


app = FastAPI(
    title=f"{_settings.app_name} API",
    description=(
        "REST API for NexGenIQ - an open-source selection-index and "
        "herd-simulation platform for beef cattle. Exposes the Index "
        "Builder and the herd-simulation MEV-derivation engines."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

# CORS: allow the local React dev server to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the API routers under the versioned prefix.
_prefix = _settings.api_v1_prefix
app.include_router(auth.router, prefix=_prefix)
app.include_router(library_routes.router, prefix=_prefix)
app.include_router(import_routes.router, prefix=_prefix)
app.include_router(index_routes.router, prefix=_prefix)
app.include_router(sim_routes.router, prefix=_prefix)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness check - confirms the API is up and reports versions."""
    return {
        "status": "ok",
        "app": _settings.app_name,
        "api_version": "0.2.0",
        "engine": _settings.engine_version,
    }
