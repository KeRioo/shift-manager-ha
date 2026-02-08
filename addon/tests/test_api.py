"""Integration tests – full API via FastAPI TestClient."""

import pytest


# ═══════════════════════════════════════════════════════════════
#  Health / root
# ═══════════════════════════════════════════════════════════════

class TestHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"

    def test_root_returns_html_or_json(self, client):
        r = client.get("/")
        assert r.status_code == 200


# ═══════════════════════════════════════════════════════════════
#  GET /api/shift_types
# ═══════════════════════════════════════════════════════════════

class TestShiftTypes:
    def test_list_types(self, client):
        r = client.get("/api/shift_types")
        assert r.status_code == 200
        data = r.json()
        assert "day8" in data
        assert "day12" in data
        assert "night12" in data
        assert data["day8"]["start"] == "07:00"


# ═══════════════════════════════════════════════════════════════
#  PUT /api/shifts/{date}
# ═══════════════════════════════════════════════════════════════

class TestPutShift:
    def test_create_shift(self, client):
        r = client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        assert r.status_code == 200
        data = r.json()
        assert data["date"] == "2026-06-01"
        assert data["type"] == "day8"
        assert data["start"] == "07:00"
        assert data["end"] == "15:00"

    def test_create_night_shift(self, client):
        r = client.put("/api/shifts/2026-06-01", json={"type": "night12"})
        assert r.status_code == 200
        assert r.json()["start"] == "19:00"
        assert r.json()["end"] == "07:00"

    def test_update_shift(self, client):
        client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        r = client.put("/api/shifts/2026-06-01", json={"type": "day12"})
        assert r.status_code == 200
        assert r.json()["type"] == "day12"

    def test_invalid_type_400(self, client):
        r = client.put("/api/shifts/2026-06-01", json={"type": "bogus"})
        assert r.status_code == 400

    def test_missing_type_422(self, client):
        r = client.put("/api/shifts/2026-06-01", json={})
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════
#  GET /api/shifts?from=&to=
# ═══════════════════════════════════════════════════════════════

class TestGetShifts:
    def test_empty_range(self, client):
        r = client.get("/api/shifts", params={"from": "2026-06-01", "to": "2026-06-30"})
        assert r.status_code == 200
        assert r.json() == []

    def test_range_with_data(self, client):
        client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        client.put("/api/shifts/2026-06-15", json={"type": "night12"})
        client.put("/api/shifts/2026-07-01", json={"type": "day12"})

        r = client.get("/api/shifts", params={"from": "2026-06-01", "to": "2026-06-30"})
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["date"] == "2026-06-01"
        assert data[1]["date"] == "2026-06-15"

    def test_missing_params_422(self, client):
        r = client.get("/api/shifts")
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════
#  GET /api/shifts/{date}
# ═══════════════════════════════════════════════════════════════

class TestGetSingleShift:
    def test_found(self, client):
        client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        r = client.get("/api/shifts/2026-06-01")
        assert r.status_code == 200
        assert r.json()["type"] == "day8"

    def test_not_found(self, client):
        r = client.get("/api/shifts/2099-01-01")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════
#  DELETE /api/shifts/{date}
# ═══════════════════════════════════════════════════════════════

class TestDeleteShift:
    def test_delete_existing(self, client):
        client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        r = client.delete("/api/shifts/2026-06-01")
        assert r.status_code == 200
        assert "Deleted" in r.json()["message"]

        # Confirm gone
        r = client.get("/api/shifts/2026-06-01")
        assert r.status_code == 404

    def test_delete_missing(self, client):
        r = client.delete("/api/shifts/2099-01-01")
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════
#  POST /api/undo
# ═══════════════════════════════════════════════════════════════

class TestUndo:
    def test_undo_nothing(self, client):
        r = client.post("/api/undo")
        assert r.status_code == 404

    def test_undo_reverts_creation(self, client):
        client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        r = client.post("/api/undo")
        assert r.status_code == 200
        assert r.json()["restored_date"] == "2026-06-01"

        # Shift should be gone
        r = client.get("/api/shifts/2026-06-01")
        assert r.status_code == 404

    def test_undo_reverts_update(self, client):
        client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        client.put("/api/shifts/2026-06-01", json={"type": "night12"})

        client.post("/api/undo")

        r = client.get("/api/shifts/2026-06-01")
        assert r.status_code == 200
        assert r.json()["type"] == "day8"

    def test_undo_chain(self, client):
        client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        client.put("/api/shifts/2026-06-01", json={"type": "night12"})

        # Undo night12 → day8
        client.post("/api/undo")
        assert client.get("/api/shifts/2026-06-01").json()["type"] == "day8"

        # Undo day8 → none
        client.post("/api/undo")
        assert client.get("/api/shifts/2026-06-01").status_code == 404

        # Nothing left
        assert client.post("/api/undo").status_code == 404


# ═══════════════════════════════════════════════════════════════
#  GET /api/history
# ═══════════════════════════════════════════════════════════════

class TestHistory:
    def test_empty(self, client):
        r = client.get("/api/history")
        assert r.status_code == 200
        assert r.json() == []

    def test_records_after_put(self, client):
        client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        r = client.get("/api/history")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["date"] == "2026-06-01"
        assert "day8" in data[0]["change"]

    def test_limit_param(self, client):
        for i in range(5):
            client.put(f"/api/shifts/2026-06-{i+1:02}", json={"type": "day8"})
        r = client.get("/api/history", params={"limit": 2})
        assert len(r.json()) == 2

    def test_history_newest_first(self, client):
        client.put("/api/shifts/2026-06-01", json={"type": "day8"})
        client.put("/api/shifts/2026-06-02", json={"type": "night12"})
        data = client.get("/api/history").json()
        assert data[0]["date"] == "2026-06-02"
        assert data[1]["date"] == "2026-06-01"


# ═══════════════════════════════════════════════════════════════
#  GET /api/next_shift
# ═══════════════════════════════════════════════════════════════

class TestNextShift:
    def test_no_shifts_404(self, client):
        r = client.get("/api/next_shift")
        assert r.status_code == 404

    def test_future_shift_returned(self, client):
        # Create a shift far in the future
        client.put("/api/shifts/2026-12-31", json={"type": "day8"})
        r = client.get("/api/next_shift")
        assert r.status_code == 200
        data = r.json()
        assert data["date"] == "2026-12-31"
        assert data["type"] == "day8"
        assert "datetime" in data

    def test_next_shift_fields(self, client):
        client.put("/api/shifts/2026-12-31", json={"type": "night12"})
        data = client.get("/api/next_shift").json()
        assert data["start"] == "19:00"
        assert data["end"] == "07:00"
        assert "T" in data["datetime"]


# ═══════════════════════════════════════════════════════════════
#  Full workflow – end-to-end scenario
# ═══════════════════════════════════════════════════════════════

class TestE2EWorkflow:
    def test_full_scenario(self, client):
        """Create → update → undo → delete → undo → verify."""
        # 1. Create day8
        r = client.put("/api/shifts/2026-07-01", json={"type": "day8"})
        assert r.json()["type"] == "day8"

        # 2. Update to night12
        r = client.put("/api/shifts/2026-07-01", json={"type": "night12"})
        assert r.json()["type"] == "night12"

        # 3. Undo → back to day8
        client.post("/api/undo")
        assert client.get("/api/shifts/2026-07-01").json()["type"] == "day8"

        # 4. Delete it
        r = client.delete("/api/shifts/2026-07-01")
        assert r.status_code == 200

        # 5. Undo delete → back to day8
        client.post("/api/undo")
        r = client.get("/api/shifts/2026-07-01")
        assert r.status_code == 200
        assert r.json()["type"] == "day8"

        # 6. History should have entries
        hist = client.get("/api/history").json()
        assert len(hist) >= 1
