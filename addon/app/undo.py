"""
Undo logic – snapshot-based reversal.

Each history entry stores `_snapshot` (the old state) as the first element
of the JSON Patch list.  Undo simply restores that snapshot.
"""

from __future__ import annotations

import json

from . import storage


def undo_last() -> dict | None:
    """
    Revert the last change recorded in history.

    1. Pop the newest history entry.
    2. Extract the ``_snapshot`` (previous state) stored inside it.
    3. Persist the restored state (or delete if empty).
    4. Remove the consumed history entry so repeated undo walks back.

    Returns ``{"message": …, "restored_date": …}`` or *None*.
    """
    entry = storage.get_last_history()
    if entry is None:
        return None

    affected_date: str = entry["date"]
    patch_data = json.loads(entry["patch"])

    # Extract the snapshot we embedded at write-time
    previous = _extract_snapshot(patch_data)

    # Persist the previous state
    if previous and previous.get("type"):
        storage.upsert_shift(
            affected_date,
            previous["type"],
            previous["start"],
            previous["end"],
        )
        msg = f"Undone → {affected_date} restored to {previous['type']}"
    else:
        storage.delete_shift(affected_date)
        msg = f"Undone → {affected_date} cleared"

    # Remove the consumed entry (next undo goes one step further)
    storage.delete_history_entry(entry["id"])

    return {"message": msg, "restored_date": affected_date}


# ── helpers ────────────────────────────────────────────────────

def _extract_snapshot(patch_data: list) -> dict:
    """Pull the ``_snapshot`` marker we injected, or return ``{}``."""
    if patch_data and isinstance(patch_data[0], dict) and "_snapshot" in patch_data[0]:
        return patch_data[0]["_snapshot"]
    return {}
