"""Shared pytest fixtures for the NexGenIQ backend test suite."""

import os
import sys

# Use a throwaway SQLite database on the local filesystem for tests, set
# before any app module is imported so the engine binds to it.
os.environ["NEXGENIQ_DATABASE_URL"] = "sqlite:////tmp/nexgeniq_pytest.db"
if os.path.exists("/tmp/nexgeniq_pytest.db"):
    os.remove("/tmp/nexgeniq_pytest.db")

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
def client():
    """A TestClient with the app lifespan run (so tables are created)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Register a researcher and return Authorization headers for them.

    A unique email per call keeps tests independent of each other.
    """
    import uuid

    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpass123",
              "full_name": "Test User", "role": "researcher"},
    )
    token = client.post(
        "/api/v1/auth/token",
        data={"username": email, "password": "testpass123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_index_request():
    """A valid two-animal index-build request body."""
    return {
        "goal": {
            "name": "Maternal weaning index",
            "basis": "per_cow_exposed",
            "components": [
                {"trait_code": "WW", "economic_weight": 0.85},
                {"trait_code": "CED", "economic_weight": 12.0},
                {"trait_code": "STAY", "economic_weight": 6.4},
            ],
        },
        "animals": [
            {"animal_id": "AAA-1842", "breed": "Angus",
             "evaluation_id": "AAA-2026",
             "epds": [
                 {"trait_code": "WW", "value": 72, "bif_accuracy": 0.85},
                 {"trait_code": "CED", "value": 14, "bif_accuracy": 0.70},
                 {"trait_code": "STAY", "value": 22, "bif_accuracy": 0.55},
             ]},
            {"animal_id": "AAA-0573", "breed": "Angus",
             "evaluation_id": "AAA-2026",
             "epds": [
                 {"trait_code": "WW", "value": 80, "bif_accuracy": 0.90},
                 {"trait_code": "CED", "value": 4, "bif_accuracy": 0.72},
                 {"trait_code": "STAY", "value": 12, "bif_accuracy": 0.60},
             ]},
        ],
        "mode": "economic_weight",
    }
