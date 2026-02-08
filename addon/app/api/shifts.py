"""API routes – shift management (CRUD + undo)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..shifts import set_shift, remove_shift, SHIFT_TYPES, validate_shift_type
from ..undo import undo_last
from .. import storage
from ..schemas import ShiftOut, ShiftUpdate, MessageOut, UndoOut
from ..events import broadcast

router = APIRouter(prefix="/api", tags=["shifts"])


@router.get("/shifts", response_model=list[ShiftOut])
def list_shifts(
    date_from: str = Query(..., alias="from", description="YYYY-MM-DD"),
    date_to: str = Query(..., alias="to", description="YYYY-MM-DD"),
):
    """Return shifts in a date range (inclusive)."""
    return storage.get_shifts(date_from, date_to)


@router.get("/shifts/{date}", response_model=ShiftOut)
def get_shift(date: str):
    """Return a single shift."""
    row = storage.get_shift(date)
    if row is None:
        raise HTTPException(404, f"No shift on {date}")
    return row


@router.put("/shifts/{date}", response_model=ShiftOut)
def update_shift(date: str, body: ShiftUpdate):
    """Create or update a shift (auto-fills start/end from type)."""
    if not validate_shift_type(body.type):
        raise HTTPException(
            400, f"Unknown shift type '{body.type}'. Valid: {list(SHIFT_TYPES)}"
        )
    result = set_shift(date, body.type)
    broadcast("shift_changed", {"date": date, "type": body.type})
    return result


@router.delete("/shifts/{date}", response_model=MessageOut)
def delete_shift(date: str):
    """Remove a shift."""
    ok = remove_shift(date)
    if not ok:
        raise HTTPException(404, f"No shift on {date}")
    broadcast("shift_deleted", {"date": date})
    return {"message": f"Deleted shift on {date}"}


@router.post("/undo", response_model=UndoOut)
def undo():
    """Undo the last change."""
    result = undo_last()
    if result is None:
        raise HTTPException(404, "Nothing to undo")
    broadcast("undo")
    return result


@router.get("/shift_types")
def list_shift_types():
    """Return available shift type definitions."""
    return SHIFT_TYPES
