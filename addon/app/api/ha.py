"""API routes – Home Assistant integration helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, HTTPException

from .. import storage
from ..schemas import NextShift

router = APIRouter(prefix="/api", tags=["ha"])


@router.get("/next_shift", response_model=NextShift)
def next_shift():
    """
    Return the next upcoming shift relative to *now*.

    Scans the next 90 days and returns the first shift whose start
    datetime is in the future.
    """
    now = datetime.utcnow()
    today = now.date()

    # Look up to 90 days ahead
    date_from = today.isoformat()
    date_to = (today + timedelta(days=90)).isoformat()

    shifts = storage.get_shifts(date_from, date_to)

    for s in shifts:
        shift_date = date.fromisoformat(s["date"])
        start_h, start_m = map(int, s["start"].split(":"))
        shift_start = datetime(shift_date.year, shift_date.month, shift_date.day, start_h, start_m)

        # For night shifts that start e.g. 19:00 – still compare to now
        if shift_start > now:
            return NextShift(
                date=s["date"],
                datetime=shift_start.strftime("%Y-%m-%dT%H:%M"),
                type=s["type"],
                start=s["start"],
                end=s["end"],
            )

    raise HTTPException(404, "No upcoming shift found in the next 90 days")
