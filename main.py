"""
Root-level entry point for the NexGenIQ backend.

This module exists so the backend can be started from the repository root
with a single, simple command — ``uvicorn main:app`` — with no directory
changes or path juggling. It is the deployment entry point (Railway,
Render, etc.); local development can still use ``uvicorn app.main:app``
from inside ``backend/``.

What it does:

* puts the ``backend/`` directory on the import path, so ``app`` (the
  FastAPI application package) resolves;
* re-exports the FastAPI ``app`` object.

The two engine packages, ``osit_index`` and ``osit_sim``, are installed
into the environment by the build step (see ``nixpacks.toml``), so they
import normally without any path setup.
"""

from __future__ import annotations

import os
import sys

# Make the backend/ directory importable so "import app..." works when
# this file is run from the repository root.
_BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# Re-export the FastAPI application. uvicorn main:app picks this up.
from app.main import app  # noqa: E402,F401
