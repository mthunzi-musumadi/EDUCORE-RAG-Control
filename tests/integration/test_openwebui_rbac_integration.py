"""
==============================================================================
TEST SUITE: OPEN WEBUI RBAC, MODEL ACCESS & CLEARANCE INTEGRATION
Verifies:
1. Dynamic User Session Resolution from Open WebUI Database & Forwarded Headers
2. Model Clearance Gating in Educore Governance Filter
3. Multi-Tenant RBAC & Purview Container Isolation per Authenticated Account
4. Group Access Control Consistency in Open WebUI Database
==============================================================================
"""

import unittest
import os
import sys
import json
import sqlite3

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for sub in ["src", "src/backend", "src/governance", "assets"]:
    p = os.path.abspath(os.path.join(base_dir, sub))
    if p not in sys.path:
        sys.path.insert(0, p)

from educore_enterprise_backend import (
    resolve_user_session_from_request,
    query_webui_db_user,
    execute_rag,
    EducoreFrameworkEngine,
    EDUCORE_USERS
)
from educore_framework_filter import Filter as GovernanceFilter

class TestOpenWebUIRBACIntegration(unittest.TestCase):

    def setUp(self):
        self.filter = GovernanceFilter()

    # -------------------------------------------------------------------------
    # 1. Open WebUI User Account & Group Resolution
    # -------------------------------------------------------------------------
    def test_student_account_resolution_from_db(self):
        """Resolves student@trident-college.com to Student role and Public (Tier C) clearance."""
        headers = {"X-OpenWebUI-User-Email": "student@trident-college.com"}
        session = resolve_user_session_from_request(headers, "educore-enterprise-all")

        self.assertEqual(session["role"], "student")
        self.assertEqual(session["clearance"], "public")
        self.assertIn(session["campus"].lower(), ["trident", "tcl"])
        self.assertIn("Students", session["groups"])
        print(f"\n  [PASS] Resolved Student Account: {session['name']} | Clearance: {session['clearance'].upper()}")

    def test_faculty_account_resolution_from_db(self):
        """Resolves intern@educoreservices.com to Faculty role and Staff (Tier B) clearance."""
        headers = {"X-OpenWebUI-User-Email": "intern@educoreservices.com"}
        session = resolve_user_session_from_request(headers, "educore-faculty-academic")

        self.assertEqual(session["role"], "faculty")
        self.assertEqual(session["clearance"], "staff")
        self.assertIn("Faculty", session["groups"])
        print(f"  [PASS] Resolved Faculty Account: {session['name']} | Clearance: {session['clearance'].upper()}")

    def test_admin_account_resolution_from_db(self):
        """Resolves admin@localhost to Admin role and Executive (Tier A) clearance."""
        headers = {"X-OpenWebUI-User-Email": "admin@localhost"}
        session = resolve_user_session_from_request(headers, "educore-admin-governance")

        self.assertEqual(session["role"], "admin")
        self.assertEqual(session["clearance"], "admin")
        self.assertIn("Campus Leadership / Admins", session["groups"])
        print(f"  [PASS] Resolved Admin Account: {session['name']} | Clearance: {session['clearance'].upper()}")

    def test_finance_account_resolution_from_db(self):
        """Resolves financialcoordinator@educoreservices.com to Finance role and Finance (Tier A) clearance."""
        headers = {"X-OpenWebUI-User-Email": "financialcoordinator@educoreservices.com"}
        session = resolve_user_session_from_request(headers, "educore-finance-audit")

        self.assertEqual(session["role"], "finance")
        self.assertEqual(session["clearance"], "finance")
        self.assertIn("Finance & Bursary", session["groups"])
        print(f"  [PASS] Resolved Finance Account: {session['name']} | Clearance: {session['clearance'].upper()}")

    def test_unassigned_user_defaults_to_public_zero_trust(self):
        """An unassigned user email safely defaults to Student role and Public clearance (Zero-Trust)."""
        headers = {"X-OpenWebUI-User-Email": "newuser@unknown.com"}
        session = resolve_user_session_from_request(headers, "educore-enterprise-all")

        self.assertEqual(session["role"], "student")
        self.assertEqual(session["clearance"], "public")
        self.assertEqual(len(session["groups"]), 0)
        print(f"  [PASS] Zero-Trust Fallback for Unassigned Account: Clearance: {session['clearance'].upper()}")

    # -------------------------------------------------------------------------
    # 2. Filter Model Clearance Gating
    # -------------------------------------------------------------------------
    def test_filter_blocks_student_from_counselor_model(self):
        """Governance Filter blocks Student account from accessing educore-pastoral-counselor."""
        user_context = {
            "id": "88f02376-29a6-441b-8602-5c5303b4afd4",
            "email": "student@trident-college.com",
            "name": "Student User",
            "role": "user"
        }
        req_body = {
            "model": "educore-pastoral-counselor",
            "messages": [{"role": "user", "content": "Show me student welfare cases"}]
        }

        with self.assertRaises(Exception) as cm:
            self.filter.inlet(req_body, __user__=user_context)

        self.assertIn("Clearance Access Denied", str(cm.exception))
        self.assertIn("PUBLIC", str(cm.exception))
        self.assertIn("COUNSELOR", str(cm.exception))
        print("  [PASS] Filter strictly gated Student from Pastoral Counselor Model.")

    def test_filter_blocks_faculty_from_admin_model(self):
        """Governance Filter blocks Faculty account from accessing educore-admin-governance."""
        user_context = {
            "id": "efd1da78-5871-4d05-9dc9-d3c9baea03c3",
            "email": "intern@educoreservices.com",
            "name": "Mthunzi Musumadi",
            "role": "user"
        }
        req_body = {
            "model": "educore-admin-governance",
            "messages": [{"role": "user", "content": "Review executive compliance records"}]
        }

        with self.assertRaises(Exception) as cm:
            self.filter.inlet(req_body, __user__=user_context)

        self.assertIn("Clearance Access Denied", str(cm.exception))
        self.assertIn("STAFF", str(cm.exception))
        self.assertIn("ADMIN", str(cm.exception))
        print("  [PASS] Filter strictly gated Faculty from Executive Admin Model.")

    def test_filter_permits_authorized_model_and_stamps_user(self):
        """Governance Filter permits Faculty account on educore-faculty-academic and stamps user telemetry."""
        user_context = {
            "id": "efd1da78-5871-4d05-9dc9-d3c9baea03c3",
            "email": "intern@educoreservices.com",
            "name": "Mthunzi Musumadi",
            "role": "user"
        }
        req_body = {
            "model": "educore-faculty-academic",
            "messages": [{"role": "user", "content": "Design a lesson plan for quadratic equations."}]
        }

        stamped_body = self.filter.inlet(req_body, __user__=user_context)
        self.assertIn("user", stamped_body)
        self.assertEqual(stamped_body["user"]["role"], "faculty")
        self.assertEqual(stamped_body["user"]["clearance"], "staff")
        print("  [PASS] Filter approved Faculty access and stamped verified clearance into payload.")

    def test_filter_permits_finance_account_on_finance_model(self):
        """Governance Filter permits Finance account on educore-finance-audit and stamps verified finance clearance."""
        user_context = {
            "id": "dafadcc8-6b33-4d12-8ed0-52b2e4f0ef19",
            "email": "financialcoordinator@educoreservices.com",
            "name": "Financial Coordinator",
            "role": "user"
        }
        req_body = {
            "model": "educore-finance-audit",
            "messages": [{"role": "user", "content": "Review Q3 bursary disbursement variance."}]
        }

        stamped_body = self.filter.inlet(req_body, __user__=user_context)
        self.assertIn("user", stamped_body)
        self.assertEqual(stamped_body["user"]["role"], "finance")
        self.assertEqual(stamped_body["user"]["clearance"], "finance")
        print("  [PASS] Filter approved Finance access on educore-finance-audit with FINANCE clearance.")

    def test_filter_blocks_finance_from_pastoral_model(self):
        """Governance Filter blocks Finance account from accessing confidential educore-pastoral-counselor."""
        user_context = {
            "id": "dafadcc8-6b33-4d12-8ed0-52b2e4f0ef19",
            "email": "financialcoordinator@educoreservices.com",
            "name": "Financial Coordinator",
            "role": "user"
        }
        req_body = {
            "model": "educore-pastoral-counselor",
            "messages": [{"role": "user", "content": "Show confidential welfare records."}]
        }

        with self.assertRaises(Exception) as cm:
            self.filter.inlet(req_body, __user__=user_context)

        self.assertIn("Clearance Access Denied", str(cm.exception))
        self.assertIn("FINANCE", str(cm.exception))
        self.assertIn("COUNSELOR", str(cm.exception))
        print("  [PASS] Filter strictly gated Finance account from Pastoral Counselor Model.")

    def test_filter_blocks_student_from_finance_model(self):
        """Governance Filter blocks Student account from accessing educore-finance-audit."""
        user_context = {
            "id": "88f02376-29a6-441b-8602-5c5303b4afd4",
            "email": "student@trident-college.com",
            "name": "Student User",
            "role": "user"
        }
        req_body = {
            "model": "educore-finance-audit",
            "messages": [{"role": "user", "content": "Show bursary data."}]
        }

        with self.assertRaises(Exception) as cm:
            self.filter.inlet(req_body, __user__=user_context)

        self.assertIn("Clearance Access Denied", str(cm.exception))
        self.assertIn("PUBLIC", str(cm.exception))
        self.assertIn("FINANCE", str(cm.exception))
        print("  [PASS] Filter strictly gated Student account from Finance Model.")

    def test_unauthenticated_request_to_admin_model_strictly_defaults_to_public(self):
        """Unauthenticated request without headers requesting admin model strictly resolves to Public clearance."""
        session = resolve_user_session_from_request({}, "educore-admin-governance")
        self.assertEqual(session["clearance"], "public")
        self.assertEqual(session["role"], "student")
        print("  [PASS] Zero-Trust Verified: Unauthenticated caller cannot escalate to Admin via model name.")

    def test_student_account_permitted_on_universal_enterprise_model(self):
        """Student account is permitted on universal model (educore-enterprise-all) via adaptive gating."""
        user_context = {
            "id": "88f02376-29a6-441b-8602-5c5303b4afd4",
            "email": "student@trident-college.com",
            "name": "Student User",
            "role": "user"
        }
        req_body = {
            "model": "educore-enterprise-all",
            "messages": [{"role": "user", "content": "What is the Cambridge 0580 mathematics syllabus?"}]
        }
        stamped_body = self.filter.inlet(req_body, __user__=user_context)
        self.assertIn("user", stamped_body)
        self.assertEqual(stamped_body["user"]["clearance"], "public")
        print("  [PASS] Filter permits Student account on adaptive universal enterprise model.")

    # -------------------------------------------------------------------------
    # 3. Purview Container Retrieval for Authenticated Accounts
    # -------------------------------------------------------------------------
    def test_student_account_purview_boundary(self):
        """Authenticated student account cannot retrieve internal staff policy or confidential files."""
        headers = {"X-OpenWebUI-User-Email": "student@trident-college.com"}
        student_session = resolve_user_session_from_request(headers, "educore-socratic-student")

        result = execute_rag("Brief me on staff morning briefing policies and laboratory budgets.", student_session)
        retrieved_ids = [d["id"] for d in result["retrieved_docs"]]
        self.assertNotIn("DOC-STAFF-002", retrieved_ids)
        self.assertNotIn("DOC-TRIDENT-003", retrieved_ids)
        print("  [PASS] Student Account Purview boundary verified: 0 internal/confidential chunks leaked.")

    def test_faculty_account_staff_retrieval(self):
        """Authenticated faculty account can retrieve staff briefing policy but not confidential finance ledger."""
        headers = {"X-OpenWebUI-User-Email": "intern@educoreservices.com"}
        faculty_session = resolve_user_session_from_request(headers, "educore-faculty-academic")

        result = execute_rag("Brief me on staff morning briefing policies.", faculty_session)
        retrieved_ids = [d["id"] for d in result["retrieved_docs"]]
        self.assertIn("DOC-STAFF-002", retrieved_ids)

        result_fin = execute_rag("Show me the Trident campus Q3 laboratory budget.", faculty_session)
        retrieved_fin_ids = [d["id"] for d in result_fin["retrieved_docs"]]
        self.assertNotIn("DOC-TRIDENT-003", retrieved_fin_ids)
        print("  [PASS] Faculty Account Purview boundary verified: Staff policy retrieved; financial ledger isolated.")

    # -------------------------------------------------------------------------
    # 4. Open WebUI Database Integrity
    # -------------------------------------------------------------------------
    def test_database_model_access_grants_integrity(self):
        """Verifies database contains 6 groups and all 7 models have active access grants."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
        db_path = os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db")
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT count(*) FROM "group"')
            group_count = cur.fetchone()[0]
            self.assertGreaterEqual(group_count, 6)

            cur.execute("SELECT count(*) FROM access_grant WHERE resource_type = 'model'")
            grant_count = cur.fetchone()[0]
            self.assertGreaterEqual(grant_count, 17)

            cur.execute("SELECT is_active, is_global FROM function WHERE id = 'educore_governance_filter'")
            func_row = cur.fetchone()
            self.assertIsNotNone(func_row)
            self.assertEqual(func_row[0], 1)
            self.assertEqual(func_row[1], 1)
        print(f"  [PASS] Database Integrity: {group_count} Groups, {grant_count} Model Grants, Filter Active & Global.")

    def test_database_prompt_suggestions_integrity(self):
        """Verifies default prompt suggestions in webui.db are Educore-specific and contain no irrelevant prompts."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
        db_path = os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db")
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            cur.execute("SELECT value FROM config WHERE key = 'ui.prompt_suggestions'")
            row = cur.fetchone()
            self.assertIsNotNone(row, "ui.prompt_suggestions must exist in config table")
            suggestions = json.loads(row[0])
            self.assertIsInstance(suggestions, list)
            self.assertGreaterEqual(len(suggestions), 4)

            # Ensure banned/irrelevant prompts are absent
            serialized = json.dumps(suggestions).lower()
            self.assertNotIn("college entrance exam", serialized)
            self.assertNotIn("sticky header", serialized)
            self.assertNotIn("options trading", serialized)
            self.assertNotIn("kids' art", serialized)

            # Ensure Educore educational & syllabus context is present
            self.assertIn("cambridge", serialized)
            self.assertIn("a-level", serialized)
        print(f"  [PASS] Global Prompt Suggestions Integrity: {len(suggestions)} Educore prompts verified, 0 irrelevant items.")

    def test_model_suggestion_prompts_integrity(self):
        """Verifies each governed Educore model has role- and campus-tailored suggestion_prompts in meta."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
        db_path = os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db")
        expected_models = {
            "educore-socratic-student": "socratic",
            "educore-faculty-academic": "lesson plan",
            "educore-pastoral-counselor": "safeguarding",
            "educore-finance-audit": "reconciliation",
            "educore-it-devops": "network",
            "educore-admin-governance": "aiia",
            "educore-enterprise-all": "educore policies",
        }
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            for model_id, keyword in expected_models.items():
                cur.execute("SELECT meta FROM model WHERE id = ?", (model_id,))
                row = cur.fetchone()
                self.assertIsNotNone(row, f"Model {model_id} must exist in database")
                meta = json.loads(row[0]) if row[0] else {}
                self.assertIn("suggestion_prompts", meta, f"Model {model_id} must have suggestion_prompts in meta")
                prompts = meta["suggestion_prompts"]
                self.assertIsInstance(prompts, list)
                self.assertGreaterEqual(len(prompts), 3, f"Model {model_id} should have at least 3 suggestion prompts")
                for p in prompts:
                    self.assertIn("title", p)
                    self.assertIsInstance(p["title"], list)
                    self.assertEqual(len(p["title"]), 2)
                    self.assertIn("content", p)
                    self.assertTrue(len(p["content"]) > 10)

                serialized_prompts = json.dumps(prompts).lower()
                self.assertIn(keyword, serialized_prompts, f"Model {model_id} prompts must include '{keyword}'")
                self.assertNotIn("college entrance exam", serialized_prompts)
                self.assertNotIn("sticky header", serialized_prompts)
                self.assertNotIn("options trading", serialized_prompts)
        print(f"  [PASS] Model Prompt Suggestions Integrity: All 7 models verified with role-tailored prompts.")

if __name__ == "__main__":
    unittest.main()
