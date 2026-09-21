"""
==============================================================================
EDUCORE SERVICES - OPEN WEBUI RBAC & CLEARANCE PROVISIONING UTILITY
Strict ISO/IEC 42001:2023 & Zambian Data Protection Act No. 3 Alignment
Configures Groups, User Memberships, Model Access Controls & Governance Filter
==============================================================================
"""

import os
import sys
import json
import time
import uuid
import sqlite3

# Set UTF-8 safe stdout for Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEBUI_DB_PATH = os.path.join(BASE_DIR, ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db")
FILTER_SCRIPT_PATH = os.path.join(BASE_DIR, "educore_framework_filter.py")

GROUPS_DEF = [
    {
        "id": "group-students-001",
        "name": "Students",
        "description": "Educore Students & Learners (Tier C - Public Clearance: Diagnostic Socratic hints only; homework answer dumping prohibited)",
    },
    {
        "id": "group-faculty-002",
        "name": "Faculty",
        "description": "Teaching Faculty & Curriculum Specialists (Tier B - Staff Clearance: Cambridge 0580 syllabus, lesson planning, rubric design; automated grading banned)",
    },
    {
        "id": "group-pastoral-003",
        "name": "Pastoral Counselors",
        "description": "Campus Pastoral Care & Student Welfare Counselors (Tier A - Pastoral Clearance: Confidential student welfare cases; egress phone/NRC masking)",
    },
    {
        "id": "group-finance-004",
        "name": "Finance & Bursary",
        "description": "Campus Bursars & Financial Operations (Tier A - Finance Clearance: Balance sheets, bursaries & FQM subsidies; Fin-01 dual-key audit notices)",
    },
    {
        "id": "group-itdevops-005",
        "name": "IT & Systems DevOps",
        "description": "Systems Administrators & Infrastructure DevOps (Tier A - Restricted IT Clearance: Restricted IT topologies, secret scanning & SAST validation)",
    },
    {
        "id": "group-execadmin-006",
        "name": "Campus Leadership / Admins",
        "description": "Campus Principals, Executive Directors & Compliance Officers (Tier A - Executive Clearance: Multi-campus governance, AIIA reviews & ISO 42001 telemetry)",
    }
]

MODELS_DEF = [
    {
        "id": "educore-socratic-student",
        "name": "Educore Socratic Tutor (Tier C - Student)",
        "description": "Student Socratic tutor enforcing diagnostic hints, cognitive bypass prevention, and Adelaide declarations.",
        "allowed_groups": ["group-students-001", "group-execadmin-006"]
    },
    {
        "id": "educore-faculty-academic",
        "name": "Educore Faculty Academic Copilot (Tier B - Educator)",
        "description": "Lesson design, rubric creation, and Cambridge 0580 syllabus alignment with Edu-03 PII de-id.",
        "allowed_groups": ["group-faculty-002", "group-execadmin-006"]
    },
    {
        "id": "educore-pastoral-counselor",
        "name": "Educore Pastoral Safeguarding Copilot (Tier A - Counselor)",
        "description": "Confidential student welfare and pastoral care review with egress NRC/phone shield.",
        "allowed_groups": ["group-pastoral-003", "group-execadmin-006"]
    },
    {
        "id": "educore-finance-audit",
        "name": "Educore Finance & Bursar Copilot (Tier A - Finance)",
        "description": "M365 Copilot Finance with Fin-01 Dual-Key manual calculation audits and FQM subsidy masking.",
        "allowed_groups": ["group-finance-004", "group-execadmin-006"]
    },
    {
        "id": "educore-it-devops",
        "name": "Educore IT & DevOps Copilot (Tier A - Restricted IT)",
        "description": "GitHub Copilot Enterprise with IT-01 pre-commit secret scanning and SAST validation.",
        "allowed_groups": ["group-itdevops-005", "group-execadmin-006"]
    },
    {
        "id": "educore-admin-governance",
        "name": "Educore Executive Governance & ISO 42001 Copilot (Tier A - Admin)",
        "description": "Executive administration, cross-campus multi-tenant oversight, and 6-Step AIIA management.",
        "allowed_groups": ["group-execadmin-006"]
    },
    {
        "id": "educore-enterprise-all",
        "name": "Educore Enterprise RAG (Universal / Staff Adaptive)",
        "description": "Adaptive enterprise model governed by ISO 42001 and Purview container controls for institutional staff.",
        "allowed_groups": [
            "group-students-001",
            "group-faculty-002",
            "group-pastoral-003",
            "group-finance-004",
            "group-itdevops-005",
            "group-execadmin-006"
        ]
    }
]

USER_MAPPINGS = {
    "admin@localhost": "group-execadmin-006",
    "intern@educoreservices.com": "group-faculty-002",
    "student@trident-college.com": "group-students-001"
}

def provision_openwebui_rbac():
    if not os.path.exists(WEBUI_DB_PATH):
        print(f"Error: Open WebUI database not found at {WEBUI_DB_PATH}")
        sys.exit(1)

    print(f"[1/5] Connecting to Open WebUI database: {WEBUI_DB_PATH}")
    con = sqlite3.connect(WEBUI_DB_PATH)
    cur = con.cursor()

    # Get admin user ID
    cur.execute("SELECT id FROM user WHERE role = 'admin' LIMIT 1")
    admin_row = cur.fetchone()
    admin_id = admin_row[0] if admin_row else "system-admin"

    now = int(time.time())

    # 1. Provision Groups
    print("[2/5] Synchronizing Organizational Role Groups...")
    for g in GROUPS_DEF:
        cur.execute('SELECT id FROM "group" WHERE id = ? OR name = ?', (g["id"], g["name"]))
        existing = cur.fetchone()
        if existing:
            cur.execute(
                'UPDATE "group" SET name = ?, description = ?, updated_at = ? WHERE id = ?',
                (g["name"], g["description"], now, existing[0])
            )
        else:
            cur.execute(
                'INSERT INTO "group" (id, user_id, name, description, data, meta, permissions, created_at, updated_at) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (g["id"], admin_id, g["name"], g["description"], json.dumps({"config": {"share": "private"}}), None, None, now, now)
            )
        print(f"  ✓ Group: {g['name']}")

    # 2. Assign Users to Groups
    print("[3/5] Assigning User Accounts to Respective Role Groups...")
    for email, target_group_id in USER_MAPPINGS.items():
        cur.execute("SELECT id, name FROM user WHERE lower(email) = ?", (email.lower(),))
        user_row = cur.fetchone()
        if not user_row:
            u_id = str(uuid.uuid4())
            name = "Student User" if "student" in email else ("Faculty Intern" if "intern" in email else email.split("@")[0].capitalize())
            role = "user"
            cur.execute(
                "INSERT INTO user (id, name, email, role, profile_image_url, last_active_at, updated_at, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (u_id, name, email.lower(), role, "/user.png", now, now, now)
            )
            user_row = (u_id, name)
        
        u_id, u_name = user_row
        # Check if membership exists
        cur.execute("SELECT id FROM group_member WHERE group_id = ? AND user_id = ?", (target_group_id, u_id))
        if not cur.fetchone():
            member_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO group_member (id, group_id, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (member_id, target_group_id, u_id, now, now)
            )
        print(f"  ✓ User {u_name} ({email}) -> Linked to {target_group_id}")

    # 3. Synchronize Models & Access Grants
    print("[4/5] Synchronizing AI Models and Group Access Controls...")
    for m in MODELS_DEF:
        cur.execute("SELECT id FROM model WHERE id = ?", (m["id"],))
        existing_m = cur.fetchone()
        meta_dict = {
            "description": m["description"],
            "profile_image_url": "/static/favicon.png",
            "capabilities": {"vision": False, "citations": True}
        }
        params_dict = {}

        if existing_m:
            cur.execute(
                "UPDATE model SET name = ?, meta = ?, updated_at = ?, is_active = 1 WHERE id = ?",
                (m["name"], json.dumps(meta_dict), now, m["id"])
            )
        else:
            cur.execute(
                "INSERT INTO model (id, user_id, base_model_id, name, params, meta, is_active, created_at, updated_at) "
                "VALUES (?, ?, NULL, ?, ?, ?, 1, ?, ?)",
                (m["id"], admin_id, m["name"], json.dumps(params_dict), json.dumps(meta_dict), now, now)
            )

        # Clear existing model access grants to ensure fresh state
        cur.execute("DELETE FROM access_grant WHERE resource_type = 'model' AND resource_id = ?", (m["id"],))

        # Insert grants for allowed groups
        for grp_id in m["allowed_groups"]:
            grant_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO access_grant (id, resource_type, resource_id, principal_type, principal_id, permission, created_at) "
                "VALUES (?, 'model', ?, 'group', ?, 'read', ?)",
                (grant_id, m["id"], grp_id, now)
            )

        print(f"  ✓ Model: {m['id']} -> Restricted to {len(m['allowed_groups'])} Group(s)")

    # 4. Register Governance Filter in Open WebUI Functions
    print("[5/5] Registering Educore AI Framework Governance Filter & Admin Valves...")
    filter_content = ""
    if os.path.exists(FILTER_SCRIPT_PATH):
        with open(FILTER_SCRIPT_PATH, "r", encoding="utf-8") as f:
            filter_content = f.read()

    func_id = "educore_governance_filter"
    func_name = "Educore AI Framework Governance & Clearance Filter"
    meta_info = {
        "description": "Strict ISO 42001 & Zambian Data Protection Act No. 3 governance filter. Links Open WebUI user roles & groups to AI clearance tiers, cognitive bypass prevention, and egress PII shielding.",
        "manifest": {}
    }
    default_valves = {
        "role_clearance_map": json.dumps({
            "Students": "public",
            "Faculty": "staff",
            "Pastoral Counselors": "counselor",
            "Finance & Bursary": "admin",
            "IT & Systems DevOps": "admin",
            "Campus Leadership / Admins": "admin"
        }),
        "default_clearance": "public",
        "enforce_model_clearance_gating": True,
        "enforce_secret_scanning": True,
        "enforce_emotion_ban": True,
        "enforce_emergency_dispatch": True,
        "enforce_hr_autonomy": True,
        "enforce_socratic_student": True,
        "enforce_fin_dual_key": True,
        "enforce_pii_redaction": True
    }

    cur.execute("SELECT id FROM function WHERE id = ?", (func_id,))
    existing_func = cur.fetchone()
    if existing_func:
        cur.execute(
            "UPDATE function SET name = ?, content = ?, meta = ?, valves = ?, is_active = 1, is_global = 1, updated_at = ? WHERE id = ?",
            (func_name, filter_content, json.dumps(meta_info), json.dumps(default_valves), now, func_id)
        )
    else:
        cur.execute(
            "INSERT INTO function (id, user_id, name, type, content, meta, valves, is_active, is_global, created_at, updated_at) "
            "VALUES (?, ?, ?, 'filter', ?, ?, ?, 1, 1, ?, ?)",
            (func_id, admin_id, func_name, filter_content, json.dumps(meta_info), json.dumps(default_valves), now, now)
        )
    print(f"  ✓ Function '{func_name}' registered as Global Active Filter.")

    con.commit()
    con.close()
    print("\n==============================================================================")
    print("  OPEN WEBUI RBAC & CLEARANCE PROVISIONING COMPLETE!")
    print("  - 6 Organizational Role Groups Active")
    print("  - 7 Governed Educore Models Configured with Access Control Lists")
    print("  - Users Linked to Respective Role Groups")
    print("  - Governance Filter Active with UI-Manageable Valves for Admin")
    print("==============================================================================")

if __name__ == "__main__":
    provision_openwebui_rbac()
