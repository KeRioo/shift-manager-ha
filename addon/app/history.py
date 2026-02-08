"""History helpers – formatting, querying."""

from __future__ import annotations

from . import storage


def get_formatted_history(limit: int = 50) -> list[dict]:
    """Return history entries formatted for the API."""
    raw = storage.get_history(limit=limit)
    out = []
    for entry in raw:
        out.append(
            {
                "id": entry["id"],
                "timestamp": entry["timestamp"],
                "date": entry["date"],
                "change": entry.get("description", ""),
            }
        )
    return out
