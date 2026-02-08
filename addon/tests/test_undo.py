"""Tests for the undo mechanism."""

import json

from app.shifts import set_shift, remove_shift
from app.undo import undo_last, _extract_snapshot
from app import storage


# ═══════════════════════════════════════════════════════════════
#  _extract_snapshot helper
# ═══════════════════════════════════════════════════════════════

class TestExtractSnapshot:
    def test_with_snapshot(self):
        data = [{"_snapshot": {"type": "day8"}}, {"op": "replace"}]
        assert _extract_snapshot(data) == {"type": "day8"}

    def test_without_snapshot(self):
        data = [{"op": "add", "path": "/type", "value": "day8"}]
        assert _extract_snapshot(data) == {}

    def test_empty_list(self):
        assert _extract_snapshot([]) == {}

    def test_snapshot_empty_dict(self):
        data = [{"_snapshot": {}}]
        assert _extract_snapshot(data) == {}


# ═══════════════════════════════════════════════════════════════
#  undo_last – single step
# ═══════════════════════════════════════════════════════════════

class TestUndoSingle:
    def test_undo_nothing(self):
        """Undo with no history returns None."""
        assert undo_last() is None

    def test_undo_new_shift_clears_it(self):
        """Creating a shift then undoing should remove it."""
        set_shift("2026-05-01", "day8")
        assert storage.get_shift("2026-05-01") is not None

        result = undo_last()
        assert result is not None
        assert result["restored_date"] == "2026-05-01"
        assert "cleared" in result["message"]

        # Shift should be gone
        assert storage.get_shift("2026-05-01") is None

    def test_undo_update_restores_old_type(self):
        """Changing a shift type then undoing should restore the original."""
        set_shift("2026-05-01", "day8")
        set_shift("2026-05-01", "night12")

        assert storage.get_shift("2026-05-01")["type"] == "night12"

        result = undo_last()
        assert result is not None

        row = storage.get_shift("2026-05-01")
        assert row is not None
        assert row["type"] == "day8"

    def test_undo_delete_restores_shift(self):
        """Removing a shift then undoing should bring it back."""
        set_shift("2026-05-01", "day12")
        remove_shift("2026-05-01")
        assert storage.get_shift("2026-05-01") is None

        result = undo_last()
        assert result is not None

        row = storage.get_shift("2026-05-01")
        assert row is not None
        assert row["type"] == "day12"


# ═══════════════════════════════════════════════════════════════
#  undo_last – multi-step
# ═══════════════════════════════════════════════════════════════

class TestUndoMultiStep:
    def test_undo_two_steps(self):
        """Undo twice should walk back through two changes."""
        set_shift("2026-05-01", "day8")     # history entry 1
        set_shift("2026-05-01", "day12")    # history entry 2
        set_shift("2026-05-01", "night12")  # history entry 3

        assert storage.get_shift("2026-05-01")["type"] == "night12"

        # Undo 3: night12 → day12
        undo_last()
        assert storage.get_shift("2026-05-01")["type"] == "day12"

        # Undo 2: day12 → day8
        undo_last()
        assert storage.get_shift("2026-05-01")["type"] == "day8"

        # Undo 1: day8 → none
        undo_last()
        assert storage.get_shift("2026-05-01") is None

    def test_undo_exhausted_returns_none(self):
        """After undoing everything, next undo returns None."""
        set_shift("2026-05-01", "day8")
        undo_last()
        assert undo_last() is None

    def test_undo_multiple_dates(self):
        """Undo should correctly handle changes across different dates."""
        set_shift("2026-05-01", "day8")
        set_shift("2026-05-02", "night12")

        # Last change was on 2026-05-02
        result = undo_last()
        assert result["restored_date"] == "2026-05-02"
        assert storage.get_shift("2026-05-02") is None

        # Next undo is on 2026-05-01
        result = undo_last()
        assert result["restored_date"] == "2026-05-01"
        assert storage.get_shift("2026-05-01") is None


# ═══════════════════════════════════════════════════════════════
#  undo consumes history entries
# ═══════════════════════════════════════════════════════════════

class TestUndoHistoryConsumption:
    def test_undo_removes_history_entry(self):
        set_shift("2026-05-01", "day8")
        assert len(storage.get_history()) == 1

        undo_last()
        assert len(storage.get_history()) == 0

    def test_undo_chain_empties_history(self):
        set_shift("2026-05-01", "day8")
        set_shift("2026-05-01", "night12")
        assert len(storage.get_history()) == 2

        undo_last()
        assert len(storage.get_history()) == 1

        undo_last()
        assert len(storage.get_history()) == 0
