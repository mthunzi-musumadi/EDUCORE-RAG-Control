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

def resolve_base_dir() -> str:
    for i, arg in enumerate(sys.argv[1:], start=1):
        if arg in ("--base-dir", "-b") and i < len(sys.argv) - 1:
            candidate = sys.argv[i + 1]
            if os.path.exists(candidate):
                return os.path.abspath(candidate)
        elif arg.startswith("--base-dir="):
            candidate = arg.split("=", 1)[1]
            if os.path.exists(candidate):
                return os.path.abspath(candidate)

    for env_key in ("BASE_DIR", "EDUCORE_BASE_DIR", "PROJECT_DIR", "EDUCORE_RAG_DIR"):
        val = os.environ.get(env_key)
        if val and os.path.exists(val):
            return os.path.abspath(val)

    script_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    cwd = os.getcwd()
    for start in (script_dir, cwd):
        curr = os.path.abspath(start)
        while True:
            if (
                os.path.exists(os.path.join(curr, "EDUCORE_AI_FRAMEWORK"))
                or os.path.exists(os.path.join(curr, "data"))
                or os.path.exists(os.path.join(curr, "assets"))
            ):
                return curr
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            curr = parent

    return os.path.abspath(os.path.join(script_dir, "..", ".."))


def resolve_webui_db_paths(base_dir: str) -> list:
    """
    Returns all valid Open WebUI webui.db database paths to synchronize.
    Prioritizes the production path (base_dir/data/openwebui/webui.db) and DATA_DIR.
    """
    candidates = []

    # 1. Explicit CLI argument
    for i, arg in enumerate(sys.argv[1:], start=1):
        if arg in ("--db-path", "--webui-db") and i < len(sys.argv) - 1:
            candidates.append(os.path.abspath(sys.argv[i + 1]))
        elif arg.startswith("--db-path="):
            candidates.append(os.path.abspath(arg.split("=", 1)[1]))

    # 2. Environment variables
    for env_var in ("WEBUI_DB_PATH",):
        val = os.environ.get(env_var)
        if val and os.path.exists(val):
            candidates.append(os.path.abspath(val))

    for env_var in ("DATA_DIR", "WEBUI_DATA_DIR"):
        val = os.environ.get(env_var)
        if val:
            candidate = os.path.join(val, "webui.db")
            if os.path.exists(candidate):
                candidates.append(os.path.abspath(candidate))

    # 3. Standard production and development project paths (data/openwebui/webui.db first)
    candidates.extend([
        os.path.join(base_dir, "data", "openwebui", "webui.db"),
        os.path.join(os.getcwd(), "data", "openwebui", "webui.db"),
        os.path.join(base_dir, "data", "webui.db"),
        os.path.join(os.getcwd(), "data", "webui.db"),
    ])

    # 4. Virtual environment & installed open_webui paths
    try:
        import open_webui
        ow_pkg_dir = os.path.dirname(os.path.abspath(open_webui.__file__))
        candidates.append(os.path.join(ow_pkg_dir, "data", "webui.db"))
    except Exception:
        pass

    candidates.extend([
        os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db"),
        os.path.join(sys.prefix, "Lib", "site-packages", "open_webui", "data", "webui.db"),
        os.path.join(sys.prefix, "data", "webui.db"),
        os.path.join(os.getcwd(), ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db"),
        os.path.expanduser("~/.open-webui/data/webui.db"),
        os.path.expanduser("~/.open-webui/webui.db"),
    ])

    found = []
    seen = set()
    for c in candidates:
        if c and os.path.exists(c):
            norm = os.path.abspath(c)
            if norm not in seen:
                seen.add(norm)
                found.append(norm)

    if not found:
        found.append(os.path.abspath(os.path.join(base_dir, "data", "openwebui", "webui.db")))

    return found


def resolve_webui_db_path(base_dir: str) -> str:
    return resolve_webui_db_paths(base_dir)[0]


BASE_DIR = resolve_base_dir()
WEBUI_DB_PATHS = resolve_webui_db_paths(BASE_DIR)
WEBUI_DB_PATH = WEBUI_DB_PATHS[0]

FILTER_SCRIPT_PATH = os.path.join(BASE_DIR, "src", "governance", "educore_framework_filter.py")
if not os.path.exists(FILTER_SCRIPT_PATH):
    # Fallback search for filter script
    if os.path.exists(os.path.join(BASE_DIR, "educore_framework_filter.py")):
        FILTER_SCRIPT_PATH = os.path.abspath(os.path.join(BASE_DIR, "educore_framework_filter.py"))
    elif os.path.exists(os.path.join(os.getcwd(), "src", "governance", "educore_framework_filter.py")):
        FILTER_SCRIPT_PATH = os.path.abspath(os.path.join(os.getcwd(), "src", "governance", "educore_framework_filter.py"))
    elif os.path.exists(os.path.join(os.getcwd(), "educore_framework_filter.py")):
        FILTER_SCRIPT_PATH = os.path.abspath(os.path.join(os.getcwd(), "educore_framework_filter.py"))
    elif os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "educore_framework_filter.py")):
        FILTER_SCRIPT_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "educore_framework_filter.py"))

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

DEFAULT_PROMPT_SUGGESTIONS = [
    {
        "title": ["Study assistance", "Cambridge IGCSE & A-Level"],
        "content": "Help me study and understand a core concept for Cambridge IGCSE or A-Level exams with guided explanations."
    },
    {
        "title": ["Lesson planning", "Cambridge syllabus alignment"],
        "content": "Help me draft a structured lesson plan aligned with Cambridge curriculum standards and differentiated classroom tasks."
    },
    {
        "title": ["Educore policies", "safeguarding & campus guidelines"],
        "content": "Explain Educore's child safeguarding and ICT acceptable use policies across our campuses."
    },
    {
        "title": ["Campus operations", "Trident, Sentinel & Frontier"],
        "content": "What are the standard operational procedures and calendar dates across Trident, Sentinel, and Frontier campuses?"
    },
    {
        "title": ["IT & systems support", "campus tech troubleshooting"],
        "content": "How do I troubleshoot campus lab connectivity or report a systems issue to Educore IT DevOps?"
    },
    {
        "title": ["Pastoral & wellbeing", "student support guidelines"],
        "content": "What pastoral care and student wellbeing resources are available for day and boarding learners at Educore schools?"
    }
]

MODELS_DEF = [
    {
        "id": "educore-socratic-student",
        "name": "Educore Socratic Tutor (Tier C - Student)",
        "description": "Student Socratic tutor enforcing diagnostic hints, cognitive bypass prevention, and Adelaide declarations.",
        "allowed_groups": ["group-students-001", "group-execadmin-006"],
        "suggestion_prompts": [
            {
                "title": ["Socratic vocabulary", "Cambridge IGCSE & A-Level"],
                "content": "Help me study key terminology and vocabulary for Cambridge IGCSE / A-Level subjects. Quiz me with Socratic questions and fill-in-the-blanks to test my understanding."
            },
            {
                "title": ["Step-by-step problem", "Socratic guidance"],
                "content": "I have a challenging math or science problem from my homework. Guide me through the method step-by-step with Socratic diagnostic hints rather than giving me the final answer."
            },
            {
                "title": ["Revise exam topic", "A-Level & IGCSE concepts"],
                "content": "Help me revise a difficult topic for my Cambridge exams (e.g. mechanics, cell biology, or organic chemistry). Ask me questions to test my grasp."
            },
            {
                "title": ["Essay structure", "planning an argument"],
                "content": "Help me structure an analytical essay for Cambridge English Literature or History following Cambridge assessment objectives. Critique my thesis and outline."
            }
        ]
    },
    {
        "id": "educore-faculty-academic",
        "name": "Educore Faculty Academic Copilot (Tier B - Educator)",
        "description": "Lesson design, rubric creation, and Cambridge 0580 syllabus alignment with Edu-03 PII de-id.",
        "allowed_groups": ["group-faculty-002", "group-execadmin-006"],
        "suggestion_prompts": [
            {
                "title": ["Lesson planning", "Cambridge 0580 syllabus"],
                "content": "Draft a 50-minute structured lesson plan aligned with Cambridge IGCSE Mathematics (0580) or Science, including differentiated learning activities."
            },
            {
                "title": ["Assessment rubric", "formative & summative criteria"],
                "content": "Generate a 4-tier assessment rubric for a Secondary or Primary coursework project with clear performance descriptors and moderation guidelines."
            },
            {
                "title": ["Differentiated tasks", "mixed-ability classroom"],
                "content": "Suggest differentiated extension and support activities for a mixed-ability class across our Sentinel and Trident campuses."
            },
            {
                "title": ["Curriculum alignment", "Cambridge & Zambian standards"],
                "content": "How do I cross-align this Cambridge curriculum unit with Zambian national syllabus requirements for our primary and secondary learners?"
            }
        ]
    },
    {
        "id": "educore-pastoral-counselor",
        "name": "Educore Pastoral Safeguarding Copilot (Tier A - Counselor)",
        "description": "Confidential student welfare and pastoral care review with egress NRC/phone shield.",
        "allowed_groups": ["group-pastoral-003", "group-execadmin-006"],
        "suggestion_prompts": [
            {
                "title": ["Safeguarding review", "pastoral care protocol"],
                "content": "Review our Educore child safeguarding policy guidelines and reporting workflow for a confidential student welfare concern."
            },
            {
                "title": ["Boarding welfare", "pastoral support strategies"],
                "content": "What are effective pastoral support interventions and wellbeing routines for secondary boarding students at Trident College?"
            },
            {
                "title": ["Restorative discussion", "resolving peer conflicts"],
                "content": "Provide a restorative conversation framework to guide a pastoral mediation session between students while ensuring emotional safety."
            },
            {
                "title": ["De-identified notes", "structuring pastoral logs"],
                "content": "Help me format a pastoral incident follow-up report adhering strictly to Zambian Data Protection Act No. 3 de-identification standards."
            }
        ]
    },
    {
        "id": "educore-finance-audit",
        "name": "Educore Finance & Bursar Copilot (Tier A - Finance)",
        "description": "M365 Copilot Finance with Fin-01 Dual-Key manual calculation audits and FQM subsidy masking.",
        "allowed_groups": ["group-finance-004", "group-execadmin-006"],
        "suggestion_prompts": [
            {
                "title": ["Fee reconciliation", "campus bursary operations"],
                "content": "Review standard reconciliation procedures for termly school fees, meal allowances, and boarding charges across Educore campuses."
            },
            {
                "title": ["FQM subsidy review", "corporate bursary guidelines"],
                "content": "Outline the audit verification checklist for First Quantum Minerals (FQM) educational subsidies and staff bursary allocations."
            },
            {
                "title": ["Procurement policy", "departmental requisitions"],
                "content": "Verify the approval thresholds, quotation requirements, and dual-key authorization workflow for campus departmental purchase requisitions."
            },
            {
                "title": ["Budget variance", "quarterly operational expenses"],
                "content": "How should campus heads of department structure their quarterly budget variance report against approved annual CAPEX/OPEX allocations?"
            }
        ]
    },
    {
        "id": "educore-it-devops",
        "name": "Educore IT & DevOps Copilot (Tier A - Restricted IT)",
        "description": "GitHub Copilot Enterprise with IT-01 pre-commit secret scanning and SAST validation.",
        "allowed_groups": ["group-itdevops-005", "group-execadmin-006"],
        "suggestion_prompts": [
            {
                "title": ["Campus network", "VLAN & Wi-Fi diagnostics"],
                "content": "Provide a diagnostic script and checklist to troubleshoot school lab Wi-Fi roaming and VLAN routing between staff and student networks."
            },
            {
                "title": ["Workstation script", "automated lab maintenance"],
                "content": "Generate a PowerShell maintenance script to verify Windows updates, clear temporary profiles, and audit software on campus computer lab machines."
            },
            {
                "title": ["School MIS audit", "backup verification"],
                "content": "Outline an automated procedure to verify daily school management system (MIS) database backups and ensure off-site encryption compliance."
            },
            {
                "title": ["IT security policy", "incident response protocol"],
                "content": "Review the incident response protocol for suspected phishing emails targeting campus staff accounts or school credentials."
            }
        ]
    },
    {
        "id": "educore-admin-governance",
        "name": "Educore Executive Governance & ISO 42001 Copilot (Tier A - Admin)",
        "description": "Executive administration, cross-campus multi-tenant oversight, and 6-Step AIIA management.",
        "allowed_groups": ["group-execadmin-006"],
        "suggestion_prompts": [
            {
                "title": ["AIIA risk review", "AI system impact assessment"],
                "content": "Guide me through conducting a 6-Step Algorithmic Impact Assessment (AIIA) for a new educational technology deployment under ISO 42001."
            },
            {
                "title": ["Multi-campus audit", "cross-campus compliance"],
                "content": "Generate a compliance audit checklist covering academic standards, health & safety, and licensing across Trident, Sentinel, and Frontier campuses."
            },
            {
                "title": ["Campus policy update", "governance harmonization"],
                "content": "Draft an executive policy memo harmonizing staff professional development and Cambridge teacher accreditation standards across all campuses."
            },
            {
                "title": ["Executive summary", "termly performance review"],
                "content": "Provide an executive briefing template summarizing termly academic progression, boarding capacity, and operational KPIs for the Educore board."
            }
        ]
    },
    {
        "id": "educore-enterprise-all",
        "name": "Educore Enterprise RAG (Universal / Adaptive)",
        "description": "Adaptive enterprise model governed by ISO 42001 and Purview container controls for all institutional roles.",
        "allowed_groups": [
            "group-students-001",
            "group-faculty-002",
            "group-pastoral-003",
            "group-finance-004",
            "group-itdevops-005",
            "group-execadmin-006"
        ],
        "suggestion_prompts": [
            {
                "title": ["Educore policies", "institutional guidelines"],
                "content": "Search and summarize Educore institutional policies regarding staff conduct, child safeguarding, and ICT acceptable use."
            },
            {
                "title": ["Campus calendar", "term dates & events"],
                "content": "What are the key academic calendar dates, exeat weekends, and assessment periods across Trident and Sentinel campuses this academic year?"
            },
            {
                "title": ["Cross-campus inquiry", "Trident, Sentinel & Frontier"],
                "content": "Explain how curricular coordination and sports fixtures are organized across Trident College, Sentinel Kabitaka, and the Prep schools."
            },
            {
                "title": ["Staff resources", "administrative procedures"],
                "content": "Where can I find the official standard operating procedures for travel requisitions, professional development requests, and HR inquiries?"
            }
        ]
    }
]

USER_MAPPINGS = {
    "admin@localhost": "group-execadmin-006",
    "intern@educoreservices.com": "group-faculty-002",
    "student@trident-college.com": "group-students-001",
    "financialcoordinator@educoreservices.com": "group-finance-004"
}

def provision_database(db_path: str):
    if not os.path.exists(db_path):
        print(f"Warning: Open WebUI database not found at {db_path}")
        return False

    print(f"\n--- [Connecting to Open WebUI database: {db_path}] ---")
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    # Get admin user ID
    cur.execute("SELECT id FROM user WHERE role = 'admin' LIMIT 1")
    admin_row = cur.fetchone()
    admin_id = admin_row[0] if admin_row else "system-admin"

    now = int(time.time())

    # 1. Provision Groups
    print("  [1/5] Synchronizing Organizational Role Groups...")
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
        print(f"    ✓ Group: {g['name']}")

    # 2. Assign Users to Groups
    print("  [2/5] Assigning User Accounts to Respective Role Groups...")
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
        print(f"    ✓ User {u_name} ({email}) -> Linked to {target_group_id}")

    # 3. Synchronize Models & Access Grants
    print("  [3/5] Synchronizing AI Models and Group Access Controls...")
    for m in MODELS_DEF:
        cur.execute("SELECT id FROM model WHERE id = ?", (m["id"],))
        existing_m = cur.fetchone()
        meta_dict = {
            "description": m["description"],
            "profile_image_url": "/static/educore-rag-e.png",
            "capabilities": {"vision": False, "citations": True},
            "suggestion_prompts": m.get("suggestion_prompts", [])
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

        print(f"    ✓ Model: {m['id']} -> Restricted to {len(m['allowed_groups'])} Group(s)")

    # 3b. Hide Raw Backend / Ollama Models (llama3.2, nomic-embed-text)
    raw_models_to_hide = [
        "llama3.2:1b",
        "llama3.2:latest",
        "llama3.2",
        "nomic-embed-text:latest",
        "nomic-embed-text"
    ]
    for raw_id in raw_models_to_hide:
        cur.execute("SELECT id FROM model WHERE id = ?", (raw_id,))
        existing_raw = cur.fetchone()
        hidden_meta = json.dumps({
            "hidden": True,
            "description": "Internal Educore inference / embedding model (gated behind Educore RAG personas)."
        })
        if existing_raw:
            cur.execute(
                "UPDATE model SET is_active = 0, meta = ?, updated_at = ? WHERE id = ?",
                (hidden_meta, now, raw_id)
            )
        else:
            cur.execute(
                "INSERT INTO model (id, user_id, base_model_id, name, params, meta, is_active, created_at, updated_at) "
                "VALUES (?, ?, NULL, ?, '{}', ?, 0, ?, ?)",
                (raw_id, admin_id, raw_id, hidden_meta, now, now)
            )
        # Ensure no access grants exist for raw models
        cur.execute("DELETE FROM access_grant WHERE resource_type = 'model' AND resource_id = ?", (raw_id,))
    print(f"    ✓ Raw Ollama models hidden ({', '.join(raw_models_to_hide)})")

    # 4. Register Governance Filter in Open WebUI Functions
    print("  [4/5] Registering Educore AI Framework Governance Filter & Admin Valves...")
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
            "Finance & Bursary": "finance",
            "IT & Systems DevOps": "devops",
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
    print(f"    ✓ Function '{func_name}' registered as Global Active Filter.")

    # 5. Disable Direct Ollama Provider & Update Default Prompt Suggestions
    cur.execute("SELECT key FROM config WHERE key = 'ollama.enable'")
    if cur.fetchone():
        cur.execute("UPDATE config SET value = 'false', updated_at = ? WHERE key = 'ollama.enable'", (now,))
    else:
        cur.execute("INSERT INTO config (key, value, updated_at) VALUES ('ollama.enable', 'false', ?)", (now,))
    print("    ✓ Open WebUI direct Ollama provider disabled (exposing only governed Educore models).")

    cur.execute("SELECT key FROM config WHERE key = 'ui.prompt_suggestions'")
    if cur.fetchone():
        cur.execute("UPDATE config SET value = ?, updated_at = ? WHERE key = 'ui.prompt_suggestions'", (json.dumps(DEFAULT_PROMPT_SUGGESTIONS), now))
    else:
        cur.execute("INSERT INTO config (key, value, updated_at) VALUES ('ui.prompt_suggestions', ?, ?)", (json.dumps(DEFAULT_PROMPT_SUGGESTIONS), now))
    print("    ✓ Open WebUI default prompt suggestions updated with Educore institutional prompts.")

    con.commit()
    con.close()

    # 6. Synchronize Branding, Logos & Laws of UX CSS
    try:
        from apply_educore_logos import apply_branding
    except ImportError:
        try:
            from src.governance.apply_educore_logos import apply_branding
        except ImportError:
            apply_branding = None

    if apply_branding:
        print(f"    [Synchronizing Educore Branding & Laws of UX CSS to {db_path}...]")
        apply_branding(base_dir=BASE_DIR, db_path=db_path)

    return True


def provision_openwebui_rbac(target_db_paths: list = None):
    paths = target_db_paths or WEBUI_DB_PATHS
    print(f"Synchronizing Open WebUI RBAC across {len(paths)} database(s)...")
    for p in paths:
        provision_database(p)

    print("\n==============================================================================")
    print("  OPEN WEBUI RBAC & CLEARANCE PROVISIONING COMPLETE!")
    print(f"  - Synchronized across: {', '.join(paths)}")
    print("  - 6 Organizational Role Groups Active")
    print("  - 7 Governed Educore Models Configured with Access Control Lists")
    print("  - Raw Ollama Models (llama3.2, nomic-embed-text) Hidden from Dropdown")
    print("  - Users Linked to Respective Role Groups")
    print("  - Governance Filter Active with UI-Manageable Valves for Admin")
    print("==============================================================================")

if __name__ == "__main__":
    provision_openwebui_rbac()
