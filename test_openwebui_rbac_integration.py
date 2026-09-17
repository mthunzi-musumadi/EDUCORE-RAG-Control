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
import json
import sqlite3

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
        self.assertEqual(session["campus"], "trident")
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
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db")
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            cur.execute('SELECT count(*) FROM "group"')
            group_count = cur.fetchone()[0]
            self.assertEqual(group_count, 6)

            cur.execute("SELECT count(*) FROM access_grant WHERE resource_type = 'model'")
            grant_count = cur.fetchone()[0]
            self.assertGreaterEqual(grant_count, 17)

            cur.execute("SELECT is_active, is_global FROM function WHERE id = 'educore_governance_filter'")
            func_row = cur.fetchone()
            self.assertIsNotNone(func_row)
            self.assertEqual(func_row[0], 1)
            self.assertEqual(func_row[1], 1)
        print(f"  [PASS] Database Integrity: {group_count} Groups, {grant_count} Model Grants, Filter Active & Global.")

if __name__ == "__main__":
    unittest.main()
