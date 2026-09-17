"""
title: Educore AI Framework Filter & Clearance Gate
author: Educore Services Limited
version: 2.0.0
license: MIT
description: Enterprise governance filter linking Open WebUI accounts and groups to Educore AI clearance levels (ISO 42001, Zambian Data Protection Act No. 3, EU AI Act).
"""

import os
import re
import json
import sqlite3
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class Filter:
    class Valves(BaseModel):
        # 1. Admin-Manageable Group & Clearance Mapping
        role_clearance_map: str = Field(
            default='{"Students": "public", "Faculty": "staff", "Pastoral Counselors": "counselor", "Finance & Bursary": "admin", "IT & Systems DevOps": "admin", "Campus Leadership / Admins": "admin"}',
            description="JSON mapping of Open WebUI Group names to Educore Clearance Tiers (public, staff, counselor, admin)."
        )
        default_clearance: str = Field(
            default="public",
            description="Default clearance tier for new or unassigned accounts (Zero-Trust fallback)."
        )
        enforce_model_clearance_gating: bool = Field(
            default=True,
            description="Strictly block requests if user clearance tier is below model required tier."
        )

        # 2. Statutory Non-Software Guardrails
        enforce_secret_scanning: bool = Field(default=True, description="Guardrail IT-01: Block prompts with API credentials or secrets.")
        enforce_emotion_ban: bool = Field(default=True, description="Guardrail Fac-01: Ban emotion tracking / facial recognition.")
        enforce_emergency_dispatch: bool = Field(default=True, description="Guardrail Fac-02: Bypass AI on physical safety / electrical emergencies.")
        enforce_hr_autonomy: bool = Field(default=True, description="Guardrail HR-01: Prohibit automated candidate rejection.")
        enforce_socratic_student: bool = Field(default=True, description="Guardrail Stu-01: Prevent cognitive bypass and force diagnostic hints for students.")
        enforce_fin_dual_key: bool = Field(default=True, description="Guardrail Fin-01: Append dual-key manual audit notice on financial calculations.")
        enforce_pii_redaction: bool = Field(default=True, description="Fin-02 & Child Protection: Redact Zambian NRCs and phone numbers.")

    CLEARANCE_LEVELS = {
        "public": 1,
        "staff": 2,
        "counselor": 3,
        "admin": 4
    }

    MODEL_REQUIRED_CLEARANCE = {
        "educore-socratic-student": "public",
        "educore-faculty-academic": "staff",
        "educore-enterprise-all": "staff",
        "educore-pastoral-counselor": "counselor",
        "educore-finance-audit": "admin",
        "educore-it-devops": "admin",
        "educore-admin-governance": "admin"
    }

    def __init__(self):
        self.valves = self.Valves()
        self.phone_regex = re.compile(
            r'(?:\+?260|0)[-.\s]*(?:9[5-7]|7[5-79])(?:[-.\s]*\d){7}\b|'
            r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b'
        )
        self.nrc_regex = re.compile(r'\b\d{6}/\d{2}/\d{1}\b')
        self.aws_regex = re.compile(r'\b(?:AKIA[0-9A-Z]{16}|aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40})\b')
        self.private_key_regex = re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', re.IGNORECASE)

    def _resolve_user_groups_and_clearance(self, user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolves the user's groups and clearance level from Open WebUI context or webui.db.
        """
        if not user:
            return {
                "email": "anonymous@localhost",
                "name": "Anonymous Operator",
                "role": "user",
                "groups": [],
                "clearance": self.valves.default_clearance
            }

        user_id = user.get("id", "")
        email = user.get("email", "").strip().lower()
        name = user.get("name", "User")
        webui_role = user.get("role", "user")

        groups = []

        # 1. Check if groups are present in user dictionary
        if "groups" in user and isinstance(user["groups"], list):
            for g in user["groups"]:
                if isinstance(g, dict):
                    groups.append(g.get("name", ""))
                elif isinstance(g, str):
                    groups.append(g)

        # 2. If not found, attempt fast SQLite query against live webui.db
        if not groups and (user_id or email):
            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                db_path = os.path.join(base_dir, ".openwebui_env", "Lib", "site-packages", "open_webui", "data", "webui.db")
                if os.path.exists(db_path):
                    con = sqlite3.connect(db_path, timeout=1.0)
                    try:
                        cur = con.cursor()
                        cur.execute(
                            'SELECT g.name FROM "group" g '
                            'JOIN group_member gm ON g.id = gm.group_id '
                            'JOIN user u ON gm.user_id = u.id '
                            'WHERE u.id = ? OR lower(u.email) = ?',
                            (user_id, email)
                        )
                        groups = [row[0] for row in cur.fetchall()]
                    finally:
                        con.close()
            except Exception:
                pass

        # 3. Parse Admin-Configured Role-Clearance Mapping Valve
        try:
            mapping = json.loads(self.valves.role_clearance_map)
        except Exception:
            mapping = {
                "Students": "public",
                "Faculty": "staff",
                "Pastoral Counselors": "counselor",
                "Finance & Bursary": "admin",
                "IT & Systems DevOps": "admin",
                "Campus Leadership / Admins": "admin"
            }

        # 4. Determine clearance
        if webui_role == "admin" or "Campus Leadership / Admins" in groups:
            clearance = "admin"
            effective_role = "admin"
        elif "IT & Systems DevOps" in groups:
            clearance = mapping.get("IT & Systems DevOps", "admin")
            effective_role = "devops"
        elif "Finance & Bursary" in groups:
            clearance = mapping.get("Finance & Bursary", "admin")
            effective_role = "finance"
        elif "Pastoral Counselors" in groups:
            clearance = mapping.get("Pastoral Counselors", "counselor")
            effective_role = "counselor"
        elif "Faculty" in groups:
            clearance = mapping.get("Faculty", "staff")
            effective_role = "faculty"
        elif "Students" in groups:
            clearance = mapping.get("Students", "public")
            effective_role = "student"
        else:
            clearance = self.valves.default_clearance
            effective_role = "student" if clearance == "public" else "faculty"

        return {
            "id": user_id,
            "email": email,
            "name": name,
            "role": effective_role,
            "webui_role": webui_role,
            "groups": groups,
            "clearance": clearance
        }

    def inlet(self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Runs before sending prompt to the LLM. Enforces role-based model clearance and guardrails.
        """
        messages = body.get("messages", [])
        if not messages:
            return body

        # Resolve authenticated user session
        user_info = self._resolve_user_groups_and_clearance(__user__)
        user_clearance = user_info["clearance"].lower()
        user_role = user_info["role"].lower()
        model_id = body.get("model", "")

        # 1. Model Clearance Gating
        if self.valves.enforce_model_clearance_gating and model_id:
            m_key = model_id.lower()
            required_tier = "public"
            for mid, tier in self.MODEL_REQUIRED_CLEARANCE.items():
                if mid in m_key:
                    required_tier = tier
                    break

            user_rank = self.CLEARANCE_LEVELS.get(user_clearance, 1)
            req_rank = self.CLEARANCE_LEVELS.get(required_tier, 1)

            if user_rank < req_rank:
                raise Exception(
                    f"🛑 [Clearance Access Denied] Your account ({user_info['email']}) has clearance '{user_clearance.upper()}', "
                    f"which is insufficient for model '{model_id}' (Requires '{required_tier.upper()}'). "
                    f"Please contact your Open WebUI Administrator to request role reassignment."
                )

        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        clean_msg = re.sub(r'<context>[\s\S]*?</context>', '', last_user_msg, flags=re.IGNORECASE)
        clean_msg = re.sub(r'<source[^>]*>[\s\S]*?</source>', '', clean_msg, flags=re.IGNORECASE)
        clean_msg = re.sub(r'<attached_files>[\s\S]*?</attached_files>', '', clean_msg, flags=re.IGNORECASE)
        lower_q = clean_msg.lower().strip()

        # 2. Guardrail IT-01: Secret Scanning
        if self.valves.enforce_secret_scanning:
            if self.aws_regex.search(last_user_msg) or self.private_key_regex.search(last_user_msg):
                raise Exception(
                    "🛑 [Guardrail IT-01 Violation] Prompt blocked: Raw API credentials, secret keys, or certificates detected."
                )

        is_policy_inquiry = bool(re.search(
            r'\b(what\s+is|what\s+are|tell\s+me\s+about|explain|why\s+is|why\s+are|is\s+there|how\s+does|is\s+it\s+allowed|are\s+we\s+allowed|is\s+it\s+permitted|can\s+we|brief\s+me|summariz\w*|overview|rules?|policy|policies|framework|compliance|audit|guidelines?|standards?|prohibit\w*|ban\w*|article\s+5)\b',
            lower_q
        ))

        # 3. Guardrail Fac-01: Emotion Tracking & Facial Recognition Ban
        if self.valves.enforce_emotion_ban and not is_policy_inquiry:
            if re.search(r'\b(emotion\s+track|facial\s+recognition|mood\s+detection|biometric\s+profiling)\b', lower_q):
                raise Exception(
                    "🛑 [Guardrail Fac-01 Violation] Strictly prohibited: Facial recognition and emotion tracking violate "
                    "Educore AI Governance Policy Sec 5 and EU AI Act Article 5."
                )

        # 4. Guardrail HR-01: Candidate Rejection Ban
        if self.valves.enforce_hr_autonomy and not is_policy_inquiry:
            if re.search(r'\b(reject\s+candidate|auto-reject|eliminate\s+applicant|terminate\s+employee\s+automatically)\b', lower_q):
                raise Exception(
                    "🛑 [Guardrail HR-01 Violation] Automated candidate rejection or termination is prohibited. "
                    "All HR decisions require certified human appraisal logs."
                )

        # 5. Guardrail Stu-01: Socratic Diagnostic Hint Intercept
        if self.valves.enforce_socratic_student and (user_clearance == "public" or user_role == "student"):
            if re.search(r'\b(give\s+me\s+the\s+answer|solve\s+this\s+completely|write\s+my\s+entire\s+essay|do\s+my\s+homework)\b', lower_q):
                socratic_instruction = (
                    "\n\n[MANDATORY SOCRATIC GUARDRAIL STU-01]: The student user is asking for direct exam answers or complete assignment completion. "
                    "DO NOT provide the final answer. Provide ONLY step-by-step diagnostic guiding hints and ask clarifying questions. "
                    "Remind the student of the Adelaide Declaration of Intellectual Ownership."
                )
                if messages and messages[0].get("role") == "system":
                    messages[0]["content"] += socratic_instruction
                else:
                    messages.insert(0, {"role": "system", "content": socratic_instruction})

        # Attach resolved user telemetry to payload so downstream server gets full identity
        body["user"] = {
            "name": user_info["name"],
            "email": user_info["email"],
            "role": user_info["role"],
            "clearance": user_info["clearance"],
            "groups": user_info["groups"]
        }

        return body

    def outlet(self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Runs on LLM output before delivering to user. Enforces egress filtering, PII masking, and dual-key audits.
        """
        messages = body.get("messages", [])
        if not messages:
            return body

        last_assistant_msg = messages[-1]
        content = last_assistant_msg.get("content", "")

        # 1. PII Redaction (Zambian Phone numbers & NRCs)
        if self.valves.enforce_pii_redaction:
            content = self.phone_regex.sub("[REDACTED_PHONE_NUMBER]", content)
            content = self.nrc_regex.sub("[REDACTED_ZAMBIAN_NRC]", content)

        # 2. Guardrail Fin-01: Dual-Key Manual Audit Notice
        if self.valves.enforce_fin_dual_key:
            if re.search(r'\b(zmw|kwacha|budget|expenditure|bursary|k\d+)\b', content, re.IGNORECASE):
                content += (
                    "\n\n> ⚖️ **Guardrail Fin-01 Dual-Key Notice**: *Independent human manual verification is required "
                    "for all AI-assisted financial figures and calculations before posting to campus ledgers.*"
                )

        last_assistant_msg["content"] = content
        return body
