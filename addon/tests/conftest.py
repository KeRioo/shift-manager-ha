"""
Shared test fixtures.

Every test gets a fresh in-memory SQLite database so tests are fully isolated.
"""

from __future__ import annotations

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Force in-memory DB BEFORE any app module touches storage ────
os.environ["DB_PATH"] = ":memory:"

from app import storage                   # noqa: E402
from app.models import Base               # noqa: E402


def _reset_db():
    """Create a brand-new in-memory engine + tables, inject into storage."""
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    # Monkey-patch storage globals so all code uses this engine
    storage._engine = engine
    storage._SessionLocal = factory


@pytest.fixture(autouse=True)
def fresh_db():
    """Automatically give every test a clean database."""
    _reset_db()
    yield


# ── FastAPI TestClient ──────────────────────────────────────────

@pytest.fixture()
def client():
    """Return a ``TestClient`` pointing at the app, with a clean DB."""
    from fastapi.testclient import TestClient
    from app.main import app

    _reset_db()
    with TestClient(app) as c:
        yield c
