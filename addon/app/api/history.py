"""API routes – change history."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..history import get_formatted_history
from ..schemas import HistoryEntry

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=list[HistoryEntry])
def list_history(limit: int = Query(50, ge=1, le=500)):
    """Return recent history entries (newest first)."""
    return get_formatted_history(limit=limit)
