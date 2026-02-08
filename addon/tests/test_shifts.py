"""Tests for shift logic (types, assignment, history recording)."""

import json
import pytest

from app.shifts import (
    SHIFT_TYPES,
    validate_shift_type,
    get_shift_times,
    set_shift,
    remove_shift,
    _describe_change,
)
from app import storage


# ═══════════════════════════════════════════════════════════════
#  Shift type definitions
# ═══════════════════════════════════════════════════════════════

class TestShiftTypes:
    def test_known_types(self):
        assert "day8" in SHIFT_TYPES
        assert "day12" in SHIFT_TYPES
        assert "night12" in SHIFT_TYPES

    def test_validate_valid(self):
        assert validate_shift_type("day8") is True
        assert validate_shift_type("night12") is True

    def test_validate_invalid(self):
        assert validate_shift_type("unknown") is False
        assert validate_shift_type("") is False

    def test_get_shift_times(self):
        assert get_shift_times("day8") == ("07:00", "15:00")
        assert get_shift_times("day12") == ("07:00", "19:00")
        assert get_shift_times("night12") == ("19:00", "07:00")

    def test_get_shift_times_unknown_raises(self):
        with pytest.raises(KeyError):
            get_shift_times("nope")


# ═══════════════════════════════════════════════════════════════
#  set_shift
# ═══════════════════════════════════════════════════════════════

class TestSetShift:
    def test_set_new_shift(self):
        result = set_shift("2026-04-01", "day8")
        assert result["date"] == "2026-04-01"
        assert result["type"] == "day8"
        assert result["start"] == "07:00"
        assert result["end"] == "15:00"

    def test_set_shift_persists_in_db(self):
        set_shift("2026-04-01", "day12")
        row = storage.get_shift("2026-04-01")
        assert row is not None
        assert row["type"] == "day12"

    def test_set_shift_records_history(self):
        set_shift("2026-04-01", "day8")
        hist = storage.get_history()
        assert len(hist) == 1
        assert hist[0]["date"] == "2026-04-01"

    def test_set_shift_history_has_snapshot(self):
        set_shift("2026-04-01", "day8")
        hist = storage.get_last_history()
        patch_data = json.loads(hist["patch"])
        # First element should be the snapshot marker
        assert "_snapshot" in patch_data[0]
        # For a new shift the snapshot should be empty
        assert patch_data[0]["_snapshot"] == {}

    def test_update_shift_keeps_snapshot_of_old(self):
        set_shift("2026-04-01", "day8")
        set_shift("2026-04-01", "night12")

        hist = storage.get_last_history()
        patch_data = json.loads(hist["patch"])
        snapshot = patch_data[0]["_snapshot"]
        assert snapshot["type"] == "day8"
        assert snapshot["start"] == "07:00"

    def test_set_shift_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown shift type"):
            set_shift("2026-04-01", "bogus")

    def test_auto_fills_start_end(self):
        result = set_shift("2026-04-01", "night12")
        assert result["start"] == "19:00"
        assert result["end"] == "07:00"

    def test_overwrite_changes_type(self):
        set_shift("2026-04-01", "day8")
        result = set_shift("2026-04-01", "day12")
        assert result["type"] == "day12"
        assert result["start"] == "07:00"
        assert result["end"] == "19:00"


# ═══════════════════════════════════════════════════════════════
#  remove_shift
# ═══════════════════════════════════════════════════════════════

class TestRemoveShift:
    def test_remove_existing(self):
        set_shift("2026-04-01", "day8")
        assert remove_shift("2026-04-01") is True
        assert storage.get_shift("2026-04-01") is None

    def test_remove_missing(self):
        assert remove_shift("2099-01-01") is False

    def test_remove_records_history(self):
        set_shift("2026-04-01", "day8")
        remove_shift("2026-04-01")
        hist = storage.get_history()
        # 1 from set + 1 from remove
        assert len(hist) == 2

    def test_remove_snapshot_has_old_state(self):
        set_shift("2026-04-01", "night12")
        remove_shift("2026-04-01")
        hist = storage.get_last_history()
        patch_data = json.loads(hist["patch"])
        snapshot = patch_data[0]["_snapshot"]
        assert snapshot["type"] == "night12"


# ═══════════════════════════════════════════════════════════════
#  _describe_change helper
# ═══════════════════════════════════════════════════════════════

class TestDescribeChange:
    def test_new_shift(self):
        desc = _describe_change("2026-04-01", {}, {"type": "day8"})
        assert "Set" in desc
        assert "day8" in desc

    def test_change_shift(self):
        desc = _describe_change(
            "2026-04-01", {"type": "day8"}, {"type": "night12"}
        )
        assert "day8" in desc
        assert "night12" in desc
        assert "→" in desc
