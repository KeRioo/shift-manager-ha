"""Core shift logic – types, validation, assignment."""

from __future__ import annotations

import json
from datetime import datetime

import jsonpatch

from . import storage

# ── Shift type definitions ──────────────────────────────────────

SHIFT_TYPES: dict[str, dict[str, str]] = {
    "day8":    {"start": "07:00", "end": "15:00"},
    "day12":   {"start": "07:00", "end": "19:00"},
    "night12": {"start": "19:00", "end": "07:00"},
}


def validate_shift_type(shift_type: str) -> bool:
    """Return True when *shift_type* is a known type key."""
    return shift_type in SHIFT_TYPES


def get_shift_times(shift_type: str) -> tuple[str, str]:
    """Return (start, end) for a given type.  Raises KeyError if unknown."""
    info = SHIFT_TYPES[shift_type]
    return info["start"], info["end"]


# ── Assign / update shift ──────────────────────────────────────

def set_shift(date: str, shift_type: str) -> dict:
    """
    Assign *shift_type* to *date*.

    • Snapshots the current state before writing.
    • Saves a JSON Patch + human-readable description into history.
    • Returns the saved shift dict.
    """
    if not validate_shift_type(shift_type):
        raise ValueError(f"Unknown shift type: {shift_type}")

    # ── snapshot (before) ──
    old = storage.get_shift(date)
    old_json = old if old else {}

    # ── write ──
    start, end = get_shift_times(shift_type)
    saved = storage.upsert_shift(date, shift_type, start, end)

    # ── diff / history ──
    # We embed the old snapshot as the first element so undo can restore it.
    new_json = saved
    patch = jsonpatch.make_patch(old_json, new_json)
    patch_list: list = json.loads(patch.to_string())
    # Prepend a private snapshot marker
    patch_list.insert(0, {"_snapshot": old_json})
    description = _describe_change(date, old_json, new_json)

    storage.add_history(
        timestamp=datetime.utcnow().isoformat(),
        date=date,
        patch=json.dumps(patch_list),
        description=description,
    )

    return saved


def remove_shift(date: str) -> bool:
    """Remove a shift from a date, recording the deletion in history."""
    old = storage.get_shift(date)
    if old is None:
        return False

    storage.delete_shift(date)

    patch = jsonpatch.make_patch(old, {})
    patch_list: list = json.loads(patch.to_string())
    patch_list.insert(0, {"_snapshot": old})
    description = f"Removed {old.get('type', '?')} from {date}"

    storage.add_history(
        timestamp=datetime.utcnow().isoformat(),
        date=date,
        patch=json.dumps(patch_list),
        description=description,
    )
    return True


# ── helpers ────────────────────────────────────────────────────

def _describe_change(date: str, old: dict, new: dict) -> str:
    old_type = old.get("type", "none")
    new_type = new.get("type", "none")
    if old_type == "none":
        return f"Set {date} → {new_type}"
    return f"{date}: {old_type} → {new_type}"
