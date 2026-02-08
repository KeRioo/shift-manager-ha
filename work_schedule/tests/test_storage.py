"""Tests for the storage (DB access) layer."""

from app import storage


# ═══════════════════════════════════════════════════════════════
#  Shifts CRUD
# ═══════════════════════════════════════════════════════════════

class TestShiftsCRUD:
    def test_upsert_creates_new(self):
        result = storage.upsert_shift("2026-03-01", "day8", "07:00", "15:00")
        assert result["date"] == "2026-03-01"
        assert result["type"] == "day8"
        assert result["start"] == "07:00"
        assert result["end"] == "15:00"

    def test_upsert_updates_existing(self):
        storage.upsert_shift("2026-03-01", "day8", "07:00", "15:00")
        updated = storage.upsert_shift("2026-03-01", "night12", "19:00", "07:00")
        assert updated["type"] == "night12"
        assert updated["start"] == "19:00"

    def test_get_shift_exists(self):
        storage.upsert_shift("2026-03-01", "day12", "07:00", "19:00")
        row = storage.get_shift("2026-03-01")
        assert row is not None
        assert row["type"] == "day12"

    def test_get_shift_missing(self):
        assert storage.get_shift("2099-01-01") is None

    def test_get_shifts_range(self):
        storage.upsert_shift("2026-03-01", "day8", "07:00", "15:00")
        storage.upsert_shift("2026-03-03", "day12", "07:00", "19:00")
        storage.upsert_shift("2026-03-10", "night12", "19:00", "07:00")

        result = storage.get_shifts("2026-03-01", "2026-03-05")
        assert len(result) == 2
        assert result[0]["date"] == "2026-03-01"
        assert result[1]["date"] == "2026-03-03"

    def test_get_shifts_empty_range(self):
        result = storage.get_shifts("2099-01-01", "2099-01-31")
        assert result == []

    def test_delete_shift_exists(self):
        storage.upsert_shift("2026-03-01", "day8", "07:00", "15:00")
        assert storage.delete_shift("2026-03-01") is True
        assert storage.get_shift("2026-03-01") is None

    def test_delete_shift_missing(self):
        assert storage.delete_shift("2099-01-01") is False


# ═══════════════════════════════════════════════════════════════
#  History CRUD
# ═══════════════════════════════════════════════════════════════

class TestHistoryCRUD:
    def test_add_and_get(self):
        hid = storage.add_history(
            "2026-03-01T10:00:00",
            "2026-03-01",
            '[{"op":"add","path":"/type","value":"day8"}]',
            "Set 2026-03-01 → day8",
        )
        assert isinstance(hid, int)

        rows = storage.get_history()
        assert len(rows) == 1
        assert rows[0]["date"] == "2026-03-01"
        assert rows[0]["description"] == "Set 2026-03-01 → day8"

    def test_get_last_history(self):
        storage.add_history("2026-03-01T10:00", "2026-03-01", "[]", "first")
        storage.add_history("2026-03-01T11:00", "2026-03-02", "[]", "second")

        last = storage.get_last_history()
        assert last is not None
        assert last["description"] == "second"

    def test_get_last_history_empty(self):
        assert storage.get_last_history() is None

    def test_delete_history_entry(self):
        hid = storage.add_history("2026-03-01T10:00", "2026-03-01", "[]", "x")
        assert storage.delete_history_entry(hid) is True
        assert storage.get_last_history() is None

    def test_delete_history_entry_missing(self):
        assert storage.delete_history_entry(99999) is False

    def test_history_limit(self):
        for i in range(10):
            storage.add_history(f"2026-03-01T{i:02}:00", "2026-03-01", "[]", f"e{i}")

        rows = storage.get_history(limit=3)
        assert len(rows) == 3
        # Newest first
        assert rows[0]["description"] == "e9"

    def test_history_order_desc(self):
        storage.add_history("2026-03-01T01:00", "2026-03-01", "[]", "first")
        storage.add_history("2026-03-01T02:00", "2026-03-02", "[]", "second")

        rows = storage.get_history()
        assert rows[0]["description"] == "second"
        assert rows[1]["description"] == "first"


# ═══════════════════════════════════════════════════════════════
#  Meta key-value store
# ═══════════════════════════════════════════════════════════════

class TestMeta:
    def test_set_and_get(self):
        storage.set_meta("version", "42")
        assert storage.get_meta("version") == "42"

    def test_get_missing(self):
        assert storage.get_meta("nonexistent") is None

    def test_overwrite(self):
        storage.set_meta("key", "old")
        storage.set_meta("key", "new")
        assert storage.get_meta("key") == "new"
