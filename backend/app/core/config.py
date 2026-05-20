"""
Application configuration for the NexGenIQ backend.

Settings are read from environment variables (or a local ``.env`` file) so
the same code runs unchanged in development and in a deployed environment.
Reference: NexGenIQ Phase 3 Part 3C.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Every field has a development-friendly default so the app starts with
    zero configuration; production deployments override via environment
    variables. The JWT secret MUST be overridden in any real deployment.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="NEXGENIQ_")

    # --- application -------------------------------------------------------
    app_name: str = "NexGenIQ"
    api_v1_prefix: str = "/api/v1"
    debug: bool = True

    # --- database ----------------------------------------------------------
    # SQLite by default for zero-config local development; a deployment sets
    # this to a PostgreSQL URL (Phase 3 Part 3C Section 3.1).
    database_url: str = "sqlite:///./nexgeniq.db"

    # --- security ----------------------------------------------------------
    # CHANGE THIS in any real deployment. JWTs signed with a known secret
    # can be forged.
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12  # 12 hours

    # --- engine ------------------------------------------------------------
    engine_version: str = "osit-index 0.1.0"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
