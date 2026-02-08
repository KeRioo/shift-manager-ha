"""Database access layer – thin wrapper around SQLAlchemy + SQLite."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional, Sequence

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Shift, History, Meta

DB_PATH = os.environ.get("DB_PATH", "work_schedule.db")

_engine = None
_SessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{DB_PATH}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(_engine)
    return _engine


def _get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_engine())
    return _SessionLocal


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Yield a transactional DB session."""
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Shifts ─────────────────────────────────────────────────────

def get_shifts(date_from: str, date_to: str) -> list[dict]:
    """Return shifts between two dates (inclusive)."""
    with get_db() as db:
        rows = (
            db.execute(
                select(Shift)
                .where(Shift.date >= date_from, Shift.date <= date_to)
                .order_by(Shift.date)
            )
            .scalars()
            .all()
        )
        return [r.to_dict() for r in rows]


def get_shift(date: str) -> Optional[dict]:
    """Return a single shift or None."""
    with get_db() as db:
        row = db.get(Shift, date)
        return row.to_dict() if row else None


def upsert_shift(date: str, shift_type: str, start: str, end: str) -> dict:
    """Insert or update a shift for a given date."""
    with get_db() as db:
        row = db.get(Shift, date)
        if row is None:
            row = Shift(date=date, type=shift_type, start=start, end=end)
            db.add(row)
        else:
            row.type = shift_type
            row.start = start
            row.end = end
        db.flush()
        return row.to_dict()


def delete_shift(date: str) -> bool:
    """Delete a shift. Returns True if it existed."""
    with get_db() as db:
        row = db.get(Shift, date)
        if row:
            db.delete(row)
            return True
        return False


# ── History ────────────────────────────────────────────────────

def add_history(timestamp: str, date: str, patch: str, description: str) -> int:
    """Append a history entry; return its id."""
    with get_db() as db:
        entry = History(
            timestamp=timestamp, date=date, patch=patch, description=description
        )
        db.add(entry)
        db.flush()
        return entry.id


def get_history(limit: int = 50) -> list[dict]:
    """Most recent history entries."""
    with get_db() as db:
        rows = (
            db.execute(select(History).order_by(History.id.desc()).limit(limit))
            .scalars()
            .all()
        )
        return [r.to_dict() for r in rows]


def get_last_history() -> Optional[dict]:
    """Return the latest history entry or None."""
    with get_db() as db:
        row = (
            db.execute(select(History).order_by(History.id.desc()).limit(1))
            .scalars()
            .first()
        )
        return row.to_dict() if row else None


def delete_history_entry(entry_id: int) -> bool:
    """Remove a history entry by id."""
    with get_db() as db:
        row = db.get(History, entry_id)
        if row:
            db.delete(row)
            return True
        return False


# ── Meta ───────────────────────────────────────────────────────

def get_meta(key: str) -> Optional[str]:
    with get_db() as db:
        row = db.get(Meta, key)
        return row.value if row else None


def set_meta(key: str, value: str) -> None:
    with get_db() as db:
        row = db.get(Meta, key)
        if row is None:
            db.add(Meta(key=key, value=value))
        else:
            row.value = value
