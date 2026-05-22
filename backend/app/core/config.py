"""
Application configuration for the NexGenIQ backend.

Settings are read from environment variables (or a local .env file) so the
same code runs unchanged in development and in a deployed environment.
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

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="NEXGENIQ_"
    )

    # --- application ------------------------------------------------------
    app_name: str = "NexGenIQ"
    api_v1_prefix: str = "/api/v1"
    # Off by default: a deployment must explicitly opt in to debug output
    # (NEXGENIQ_DEBUG=true) so verbose errors are never leaked by accident.
    debug: bool = False

    # --- database ---------------------------------------------------------
    # SQLite by default for zero-config local development; a deployment
    # sets this to a PostgreSQL URL (Phase 3 Part 3C Section 3.1).
    database_url: str = "sqlite:///./nexgeniq.db"

    # --- security ---------------------------------------------------------
    # CHANGE THIS in any real deployment. JWTs signed with a known secret
    # can be forged.
    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12  # 12 hours

    # --- CORS -------------------------------------------------------------
    # Origins allowed to call the API from a browser. Defaults cover the
    # local dev servers; a deployment sets NEXGENIQ_CORS_ORIGINS to its
    # real frontend URL (comma-separated for more than one).
    cors_origins: str = (
        "http://localhost:5173,http://localhost:3000,"
        "http://127.0.0.1:5173"
    )

    # --- engine -----------------------------------------------------------
    engine_version: str = "osit-index 0.2.0"

    # --- simulation concurrency -------------------------------------------
    # A herd simulation is CPU-bound and runs for tens of seconds. This
    # caps how many run at once so a burst of users does not slow every
    # run down; requests over the cap get a clear "server busy" response.
    # Set roughly to the number of CPU cores available to the backend.
    max_concurrent_simulations: int = 2

    # --- admin bootstrap --------------------------------------------------
    # The email of the designated site administrator. On startup the
    # account with this email is promoted to the site_admin role, so the
    # admin panel has exactly one admin to begin with without any manual
    # database step. Leave blank to disable automatic promotion.
    admin_email: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        """The CORS origins as a list, parsed from the comma-separated
        string."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
