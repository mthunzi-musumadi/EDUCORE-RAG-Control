# ==============================================================================
# TEST SUITE: AUDIT LOG ENRICHMENT & QUARANTINE API ENDPOINT
# ISO/IEC 42001:2023 Clause 7.5 & Annex A.6.2.8
# Zambian Data Protection Act No. 3 of 2021
# ==============================================================================
import os
import sys
import json
import time
import shutil
import tempfile
import threading
import http.client
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "src", "backend")
for p in (BASE_DIR, BACKEND_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from educore_enterprise_backend import (
    log_audit,
    CLEARANCE_SHARDS,
    EDUCORE_USERS,
    execute_rag,
)


# ==============================================================================
# 1. AUDIT LOG ENRICHMENT — physical_gate block
# ==============================================================================
class TestAuditLogEnrichment:
    """Verify that log_audit writes a physical_gate block with shard traceability."""

    def _read_last_audit_entry(self, audit_path: str) -> dict:
        entries = []
        with open(audit_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line.strip()))
                    except Exception:
                        pass
        assert entries, "Audit log must have at least one entry"
        return entries[-1]

    def test_log_audit_writes_physical_gate_block(self, tmp_path):
        """log_audit should include a physical_gate key with queried_shards."""
        audit_file = tmp_path / "audit.jsonl"
        os.environ["EDUCORE_AUDIT_LOG"] = str(audit_file)

        fake_session = EDUCORE_USERS.get("student") or {
            "clearance": "public", "role": "student", "campus": "Ndola"
        }
        log_audit(
            user_session=fake_session,
            query="What are the student handbook policies?",
            docs=[],
            response="Here is what I found...",
            latency_ms=123.4,
            decision="CONVERSATIONAL_RESTRICTED",
            queried_shard_names=["educore_shard_public"]
        )

        entry = self._read_last_audit_entry(str(audit_file))
        assert "physical_gate" in entry, "Audit entry must contain physical_gate block"
        gate = entry["physical_gate"]
        assert gate["shard_isolation_enforced"] is True
        assert "educore_shard_public" in gate["queried_shards"]
        assert isinstance(gate["unauthorized_shards_blocked"], list)

    def test_physical_gate_blocks_higher_clearance_shards(self, tmp_path):
        """Shards not queried (because user lacks clearance) should appear in unauthorized_shards_blocked."""
        audit_file = tmp_path / "audit.jsonl"
        os.environ["EDUCORE_AUDIT_LOG"] = str(audit_file)

        fake_session = {"clearance": "public", "role": "student", "campus": "Lusaka"}
        queried = ["educore_shard_public"]
        log_audit(
            user_session=fake_session,
            query="Show me finance reports",
            docs=[],
            response="Access denied.",
            latency_ms=50.0,
            decision="CONVERSATIONAL_RESTRICTED",
            queried_shard_names=queried
        )

        entry = self._read_last_audit_entry(str(audit_file))
        blocked = entry["physical_gate"]["unauthorized_shards_blocked"]
        # All shards except public should be blocked for a public user
        for clearance in ["staff", "counselor", "finance", "devops", "admin"]:
            assert clearance in blocked, f"{clearance} shard should appear in unauthorized_shards_blocked"

    def test_physical_gate_admin_has_no_blocked_shards(self, tmp_path):
        """An admin user querying all shards should have an empty unauthorized_shards_blocked list."""
        audit_file = tmp_path / "audit.jsonl"
        os.environ["EDUCORE_AUDIT_LOG"] = str(audit_file)

        fake_session = {"clearance": "admin", "role": "admin", "campus": "HQ"}
        all_shard_names = [f"educore_shard_{c}" for c in CLEARANCE_SHARDS]
        log_audit(
            user_session=fake_session,
            query="Executive dashboard summary",
            docs=[],
            response="Here is the full summary.",
            latency_ms=200.0,
            decision="PERMITTED_RAG",
            queried_shard_names=all_shard_names
        )

        entry = self._read_last_audit_entry(str(audit_file))
        blocked = entry["physical_gate"]["unauthorized_shards_blocked"]
        assert blocked == [], f"Admin should block no shards, got: {blocked}"

    def test_no_shard_names_yields_empty_queried_shards(self, tmp_path):
        """Calling log_audit with no queried_shard_names should produce empty list (not crash)."""
        audit_file = tmp_path / "audit.jsonl"
        os.environ["EDUCORE_AUDIT_LOG"] = str(audit_file)

        fake_session = {"clearance": "staff", "role": "teacher", "campus": "Kitwe"}
        log_audit(
            user_session=fake_session,
            query="What is the attendance policy?",
            docs=[],
            response="See policy doc.",
            latency_ms=80.0,
            decision="CONVERSATIONAL_GREETING",
            queried_shard_names=None   # <-- not a RAG call
        )

        entry = self._read_last_audit_entry(str(audit_file))
        gate = entry["physical_gate"]
        assert gate["queried_shards"] == []
        assert gate["shard_isolation_enforced"] is True

    def test_compliance_annotation_present(self, tmp_path):
        """Audit entry must include the compliance annotation string."""
        audit_file = tmp_path / "audit.jsonl"
        os.environ["EDUCORE_AUDIT_LOG"] = str(audit_file)

        fake_session = {"clearance": "public", "role": "student", "campus": "Ndola"}
        log_audit(
            user_session=fake_session,
            query="Test",
            docs=[],
            response="OK",
            latency_ms=10.0,
            decision="CONVERSATIONAL_GREETING"
        )

        entry = self._read_last_audit_entry(str(audit_file))
        assert "compliance" in entry
        assert "42001" in entry["compliance"]
        assert "Zambian" in entry["compliance"]


# ==============================================================================
# 2. QUARANTINE API ENDPOINT — /api/framework/quarantine
# ==============================================================================
def _start_test_server(port: int):
    """Start the HTTP server in a background thread for endpoint tests."""
    import educore_enterprise_backend as backend
    server = backend.EducoreHTTPServer(("127.0.0.1", port), backend.EducoreRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)  # Give the server time to bind
    return server


class TestQuarantineAPIEndpoint:
    """Verify /api/framework/quarantine returns correctly shaped JSON with RBAC enforcement."""

    @pytest.fixture(autouse=True)
    def quarantine_dir(self, tmp_path, monkeypatch):
        """Create a temp quarantine dir and inject a sample event."""
        q_dir = tmp_path / "quarantine"
        q_dir.mkdir()
        monkeypatch.setenv("EDUCORE_QUARANTINE_DIR", str(q_dir))

        # Write a sample quarantine audit event
        sample_event = {
            "timestamp": "2026-09-23T09:00:00Z",
            "filename": "secret_budget.xlsx",
            "detected_clearance": "finance",
            "folder_clearance": "public",
            "reason": "clearance_mismatch",
            "quarantined_file": str(q_dir / "secret_budget.xlsx.quarantine")
        }
        log_path = q_dir / "quarantine_audit.jsonl"
        log_path.write_text(json.dumps(sample_event) + "\n", encoding="utf-8")

        # Drop a dummy quarantined file
        (q_dir / "secret_budget.xlsx.quarantine").write_text("binary content placeholder")
        self.q_dir = q_dir
        return q_dir

    def _get_token(self, role: str) -> str:
        """Return API token for a user with the specified clearance."""
        for uid, us in EDUCORE_USERS.items():
            if us.get("clearance") == role or us.get("role") == role:
                return us.get("api_key") or us.get("token") or uid
        return "no-token"

    def test_quarantine_endpoint_returns_200_for_staff(self):
        """Staff+ users should receive a 200 with quarantine event data."""
        port = 18771
        server = _start_test_server(port)
        try:
            token = self._get_token("staff")
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/api/framework/quarantine", headers={"Authorization": f"Bearer {token}"})
            resp = conn.getresponse()
            assert resp.status == 200, f"Expected 200 for staff, got {resp.status}"
            body = json.loads(resp.read().decode("utf-8"))
            assert "events" in body
            assert "quarantine_dir" in body
            assert "total_events" in body
            assert body["total_events"] >= 1
        finally:
            server.shutdown()

    def test_quarantine_endpoint_returns_403_for_public(self):
        """Unauthenticated/public requests must be rejected with 403."""
        port = 18772
        server = _start_test_server(port)
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/api/framework/quarantine", headers={"Authorization": "Bearer public-token-xyz"})
            resp = conn.getresponse()
            assert resp.status == 403, f"Expected 403 for public token, got {resp.status}"
            body = json.loads(resp.read().decode("utf-8"))
            assert "error" in body
            assert body["error"] == "Forbidden"
        finally:
            server.shutdown()

    def test_quarantine_event_has_still_quarantined_flag(self):
        """Each event in the response should include a still_quarantined boolean."""
        port = 18773
        server = _start_test_server(port)
        try:
            token = self._get_token("admin")
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/api/framework/quarantine", headers={"Authorization": f"Bearer {token}"})
            resp = conn.getresponse()
            body = json.loads(resp.read().decode("utf-8"))
            assert body["total_events"] >= 1
            event = body["events"][0]
            assert "still_quarantined" in event, "Each event must include still_quarantined flag"
            assert isinstance(event["still_quarantined"], bool)
        finally:
            server.shutdown()

    def test_quarantine_endpoint_empty_when_no_log(self, tmp_path, monkeypatch):
        """When no quarantine_audit.jsonl exists, endpoint returns 0 events gracefully."""
        empty_q = tmp_path / "empty_quarantine"
        empty_q.mkdir()
        monkeypatch.setenv("EDUCORE_QUARANTINE_DIR", str(empty_q))
        port = 18774
        server = _start_test_server(port)
        try:
            token = self._get_token("admin")
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("GET", "/api/framework/quarantine", headers={"Authorization": f"Bearer {token}"})
            resp = conn.getresponse()
            assert resp.status == 200
            body = json.loads(resp.read().decode("utf-8"))
            assert body["total_events"] == 0
            assert body["events"] == []
        finally:
            server.shutdown()
