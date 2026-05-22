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
    saved_routes,
    sim_routes,
)
from app.core.config import get_settings
from app.core.database import init_db

_settings = get_settings()


# Records whether database initialisation succeeded, so /health can
# report it instead of the whole app crashing on a bad DB connection.
_db_ready = False
_db_error = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - create database tables on startup.

    Database initialisation is wrapped so that a connection problem does
    NOT crash the whole app on startup (which would make the deployment's
    health check fail with no useful signal). Instead the app still comes
    up, and /health reports the database as unavailable.
    """
    global _db_ready, _db_error
    try:
        init_db()
        _db_ready = True
    except Exception as exc:  # noqa: BLE001 - report any startup DB failure
        _db_ready = False
        _db_error = str(exc)
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

# CORS: only the configured frontend origins may make browser requests
# to this API. Allowing any origin together with allow_credentials=True
# would let any website a logged-in user visits call this API with their
# credentials, so the allow-list is explicit.
#
# The origins come from settings.cors_origin_list, driven by the
# NEXGENIQ_CORS_ORIGINS environment variable. Local-development origins
# (localhost:5173 etc.) are covered by the default; a deployment sets
# NEXGENIQ_CORS_ORIGINS to its real frontend URL (comma-separated for
# more than one), with no trailing slash.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origin_list,
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
app.include_router(saved_routes.router, prefix=_prefix)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness check - confirms the API is up and reports versions.

    Always returns HTTP 200 when the app process is running, so a
    deployment health check passes as soon as the API is alive. The
    ``database`` field reports whether the database connected; if it did
    not, ``database_error`` carries the reason - this surfaces a
    misconfigured DATABASE_URL without crashing the whole service.
    """
    body = {
        "status": "ok",
        "app": _settings.app_name,
        "api_version": "0.2.0",
        "engine": _settings.engine_version,
        "database": "connected" if _db_ready else "unavailable",
    }
    if not _db_ready and _db_error:
        body["database_error"] = _db_error
    return body
