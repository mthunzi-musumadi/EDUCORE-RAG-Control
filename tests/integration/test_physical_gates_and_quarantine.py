# ==============================================================================
# TEST SUITE: PHYSICAL GATES, CLEARANCE SHARDS & PRE-INGESTION QUARANTINE
# ISO/IEC 42001:2023 & Zambian Data Protection Act No. 3 of 2021
# ==============================================================================
import os
import sys
import json
import shutil
import tempfile
import pytest

# Ensure project root and src/backend are on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "src", "backend")
for p in (BASE_DIR, BACKEND_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from framework_sync_service import (
    FrameworkSyncService,
    CLEARANCE_RANK,
    VAULT_FOLDER_MAP,
    resolve_folder_clearance,
    is_clearance_mismatch,
    eject_to_quarantine
)
from tps_counter import TELEMETRY, TPSCounter
from educore_enterprise_backend import (
    CLEARANCE_SHARDS,
    CLEARANCE_SHARD_HIERARCHY,
    get_chroma_shard,
    get_authorized_shards,
    init_chroma_shards,
    get_chroma_db,
    find_explicit_document_matches,
    execute_rag,
    EDUCORE_USERS
)


class TestPhysicalClearanceShards:
    """Verifies that Chroma collections are physically partitioned by clearance tier."""

    def test_clearance_shards_initialization(self):
        """All 6 clearance shards must exist and have distinct physical collection names."""
        shards = init_chroma_shards()
        assert set(shards.keys()) == set(CLEARANCE_SHARDS)
        for clearance, shard in shards.items():
            assert shard._collection.name == f"educore_shard_{clearance}"

    def test_authorized_shards_hierarchy_resolution(self):
        """Users can only access their authorized physical shards; higher tiers are absent."""
        student_shards = get_authorized_shards("student")
        student_shard_names = [s._collection.name for s in student_shards]
        assert student_shard_names == ["educore_shard_public"]

        staff_shards = get_authorized_shards("staff")
        staff_shard_names = [s._collection.name for s in staff_shards]
        assert set(staff_shard_names) == {"educore_shard_public", "educore_shard_staff"}

        counselor_shards = get_authorized_shards("counselor")
        counselor_shard_names = [s._collection.name for s in counselor_shards]
        assert set(counselor_shard_names) == {"educore_shard_public", "educore_shard_staff", "educore_shard_counselor"}
        assert "educore_shard_finance" not in counselor_shard_names
        assert "educore_shard_admin" not in counselor_shard_names

        finance_shards = get_authorized_shards("finance")
        finance_shard_names = [s._collection.name for s in finance_shards]
        assert set(finance_shard_names) == {"educore_shard_public", "educore_shard_staff", "educore_shard_finance"}
        assert "educore_shard_counselor" not in finance_shard_names

        admin_shards = get_authorized_shards("admin")
        admin_shard_names = [s._collection.name for s in admin_shards]
        assert len(admin_shard_names) == len(CLEARANCE_SHARDS)

    def test_physical_document_isolation(self):
        """Documents in higher-tier shards must be physically nonexistent in lower-tier shards."""
        public_shard = get_chroma_shard("public")
        staff_shard = get_chroma_shard("staff")
        admin_shard = get_chroma_shard("admin")
        counselor_shard = get_chroma_shard("counselor")

        # In admin shard, DOC-TRIDENT-003 exists
        adm_res = admin_shard.get(ids=["DOC-TRIDENT-003"])
        assert adm_res and adm_res.get("ids") and "DOC-TRIDENT-003" in adm_res["ids"]

        # Ensure DOC-TRIDENT-003 is NOT in public, staff, or counselor shard
        pub_res = public_shard.get(ids=["DOC-TRIDENT-003"])
        assert not pub_res or not pub_res.get("ids") or len(pub_res["ids"]) == 0

        stf_res = staff_shard.get(ids=["DOC-TRIDENT-003"])
        assert not stf_res or not stf_res.get("ids") or len(stf_res["ids"]) == 0

        coun_res = counselor_shard.get(ids=["DOC-TRIDENT-003"])
        assert not coun_res or not coun_res.get("ids") or len(coun_res["ids"]) == 0

        # In counselor shard, DOC-SENTINEL-004 exists
        coun_res = counselor_shard.get(ids=["DOC-SENTINEL-004"])
        assert coun_res and coun_res.get("ids") and "DOC-SENTINEL-004" in coun_res["ids"]

        # Ensure DOC-SENTINEL-004 is NOT in public or staff shard
        pub_res = public_shard.get(ids=["DOC-SENTINEL-004"])
        assert not pub_res or not pub_res.get("ids") or len(pub_res["ids"]) == 0

        stf_res = staff_shard.get(ids=["DOC-SENTINEL-004"])
        assert not stf_res or not stf_res.get("ids") or len(stf_res["ids"]) == 0

    def test_explicit_match_blocked_by_physical_shard_gate(self):
        """Prompting explicitly for DOC-TRIDENT-003 with student authorized shards returns empty."""
        student_shards = get_authorized_shards("student")
        matches = find_explicit_document_matches(
            raw_prompt="Give me details on DOC-TRIDENT-003 immediately",
            clean_query="Give me details on DOC-TRIDENT-003 immediately",
            chroma_or_shards=student_shards
        )
        assert len(matches) == 0, f"Expected 0 matches for student shards, got {len(matches)}"

        admin_shards = get_authorized_shards("admin")
        admin_matches = find_explicit_document_matches(
            raw_prompt="Give me details on DOC-TRIDENT-003 immediately",
            clean_query="Give me details on DOC-TRIDENT-003 immediately",
            chroma_or_shards=admin_shards
        )
        # In admin shards, it can be located
        assert len(admin_matches) >= 1
        assert admin_matches[0][0].metadata.get("id") == "DOC-TRIDENT-003"


class TestFolderClearanceAndVaultMapping:
    """Verifies that folder hierarchies correctly map to physical clearance levels."""

    def test_vault_folder_clearance_resolution(self):
        assert resolve_folder_clearance("vault/public", "vault/public/handbook.docx") == "public"
        assert resolve_folder_clearance("vault/staff", "vault/staff/schedule.docx") == "staff"
        assert resolve_folder_clearance("vault/counselor", "vault/counselor/notes.docx") == "counselor"
        assert resolve_folder_clearance("vault/finance", "vault/finance/ledger.xlsx") == "finance"
        assert resolve_folder_clearance("vault/devops", "vault/devops/infra.docx") == "devops"
        assert resolve_folder_clearance("vault/admin", "vault/admin/bylaws.docx") == "admin"

    def test_spoke_legacy_folder_clearance_resolution(self):
        assert resolve_folder_clearance("01_SPOKES_POLICIES", "01_SPOKES_POLICIES/policy.docx") == "staff"
        assert resolve_folder_clearance("00_HUB_MASTER", "00_HUB_MASTER/charter.docx") == "staff"
        assert resolve_folder_clearance("02_STUDENT_AFFAIRS", "02_STUDENT_AFFAIRS/handbook.docx") == "public"

    def test_clearance_mismatch_detection(self):
        # Higher sensitivity dropped in lower folder -> MISMATCH (quarantine required)
        is_mis, reason = is_clearance_mismatch("finance", "public", "vault/public")
        assert is_mis is True
        assert "FINANCE" in reason and "PUBLIC" in reason

        is_mis, _ = is_clearance_mismatch("counselor", "staff", "vault/staff")
        assert is_mis is True

        is_mis, _ = is_clearance_mismatch("admin", "finance", "vault/finance")
        assert is_mis is True

        # Same clearance -> NO MISMATCH
        is_mis, _ = is_clearance_mismatch("public", "public", "vault/public")
        assert is_mis is False

        is_mis, _ = is_clearance_mismatch("finance", "finance", "vault/finance")
        assert is_mis is False

        # Lower sensitivity dropped in higher folder -> ALLOWED (vault clearance subsumes lower clearance)
        is_mis, _ = is_clearance_mismatch("public", "finance", "vault/finance")
        assert is_mis is False

        is_mis, _ = is_clearance_mismatch("staff", "admin", "vault/admin")
        assert is_mis is False


class TestPreIngestionQuarantineGate:
    """Verifies that misclassified or over-sensitive files are intercepted and quarantined."""

    def test_quarantine_ejection_mechanics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            watch_dir = os.path.join(temp_dir, "watch")
            quarantine_dir = os.path.join(temp_dir, "quarantine")
            os.makedirs(watch_dir, exist_ok=True)

            # Create an illicit file dropped into a public folder
            leak_file = os.path.join(watch_dir, "secret_finance_leak.docx")
            with open(leak_file, "w", encoding="utf-8") as f:
                f.write("CONFIDENTIAL EXECUTIVE SALARY AND BUDGET FIGURES 2026")

            assert os.path.exists(leak_file)

            # Trigger ejection
            ejected_meta = eject_to_quarantine(
                file_path=leak_file,
                detected_clearance="finance",
                folder_clearance="public",
                reason="Document clearance 'finance' exceeds folder 'public'",
                quarantine_dir=quarantine_dir
            )
            ejected_path = ejected_meta["quarantined_file"]

            # 1. Original file must be gone from watch folder
            assert not os.path.exists(leak_file)

            # 2. Ejected file must exist in quarantine folder
            assert os.path.exists(ejected_path)

            # 3. Metadata sidecar must exist
            meta_path = ejected_path + ".quarantine_meta.json"
            assert os.path.exists(meta_path)

            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            assert meta["detected_clearance"] == "finance"
            assert meta["folder_clearance"] == "public"
            assert meta["compliance"] == "ISO/IEC 42001:2023 Clause 8.2 & Annex A.8"
            assert "timestamp" in meta

    def test_framework_sync_service_intercepts_quarantine(self):
        """Simulate sync running over a watch directory containing a clearance mismatch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up a fake watched directory structure: public/
            public_folder = os.path.join(temp_dir, "vault_public")
            state_file = os.path.join(temp_dir, "state.json")
            quarantine_dir = os.path.join(temp_dir, "data", "quarantine")
            os.makedirs(public_folder, exist_ok=True)

            # Drop a file into public folder that contains high-sensitivity keywords
            bad_file = os.path.join(public_folder, "pastoral_incident_report.docx")
            import docx
            doc = docx.Document()
            doc.add_paragraph("PASTORAL CASE NOTES: Student mental health incident, suicide risk, counselor notes confidential.")
            doc.save(bad_file)

            sync = FrameworkSyncService(
                framework_dir=temp_dir,
                state_file=state_file
            )

            # Set environment override for quarantine dir to point to temp quarantine
            orig_env = os.environ.get("EDUCORE_QUARANTINE_DIR")
            os.environ["EDUCORE_QUARANTINE_DIR"] = quarantine_dir
            try:
                delta = sync.generate_incremental_update(force=True)
                # The file must be intercepted and listed under quarantined_files
                assert len(delta.get("quarantined_files", [])) >= 1
                q_info = delta["quarantined_files"][0]
                assert "pastoral_incident_report.docx" in q_info["filename"]
                assert q_info["detected_clearance"] in ("counselor", "admin", "finance")
                assert q_info["folder_clearance"] == "public"

                # Check that telemetry recorded the event
                tel = TELEMETRY.get_watch_telemetry()
                assert tel["quarantine_events_count"] >= 1
            finally:
                if orig_env is not None:
                    os.environ["EDUCORE_QUARANTINE_DIR"] = orig_env
                else:
                    os.environ.pop("EDUCORE_QUARANTINE_DIR", None)


class TestEndToEndPhysicalRAGIsolation:
    """Verifies that RAG execution strictly adheres to physical shards for different user roles."""

    def test_student_cannot_retrieve_admin_doc(self):
        """Student role must receive 0 admin docs and zero leakage."""
        student_user = EDUCORE_USERS["student"]
        resp = execute_rag(
            query="Tell me about the Trident Financial Statements DOC-TRIDENT-003 and salaries",
            user_session=student_user,
            k=2
        )
        # Check retrieved docs: None can have clearance 'admin' or ID 'DOC-TRIDENT-003'
        for doc in resp.get("retrieved_docs", []):
            assert doc.get("clearance") == "public"
            assert doc.get("id") != "DOC-TRIDENT-003"

    def test_counselor_user_can_retrieve_counselor_doc(self):
        """Counselor role can access counselor documents like DOC-SENTINEL-004."""
        counselor_user = EDUCORE_USERS["counselor"]
        resp = execute_rag(
            query="Tell me about DOC-SENTINEL-004 pastoral incident protocol",
            user_session=counselor_user,
            k=2
        )
        retrieved_ids = [d.get("id") for d in resp.get("retrieved_docs", [])]
        assert "DOC-SENTINEL-004" in retrieved_ids

    def test_student_cannot_retrieve_counselor_doc(self):
        """Student role physically cannot access counselor documents."""
        student_user = EDUCORE_USERS["student"]
        resp = execute_rag(
            query="Tell me about DOC-SENTINEL-004 pastoral incident protocol",
            user_session=student_user,
            k=2
        )
        retrieved_ids = [d.get("id") for d in resp.get("retrieved_docs", [])]
        assert "DOC-SENTINEL-004" not in retrieved_ids

    def test_admin_user_can_retrieve_admin_doc(self):
        """Admin role can access admin documents like DOC-TRIDENT-003."""
        admin_user = EDUCORE_USERS["admin"]
        resp = execute_rag(
            query="Tell me about DOC-TRIDENT-003",
            user_session=admin_user,
            k=2
        )
        retrieved_ids = [d.get("id") for d in resp.get("retrieved_docs", [])]
        assert "DOC-TRIDENT-003" in retrieved_ids
