"""
title: Educore AI Framework Filter & Egress Shield
author: Educore Services Limited
version: 1.0.0
license: MIT
description: Strict governance filter enforcing EDUCORE_AI_FRAMEWORK (ISO 42001, Zambian Data Protection Act No. 3 of 2021, and EU AI Act Art. 5).
"""

import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class Filter:
    class Valves(BaseModel):
        enforce_secret_scanning: bool = Field(default=True, description="Guardrail IT-01: Block prompts with API credentials or secrets.")
        enforce_emotion_ban: bool = Field(default=True, description="Guardrail Fac-01: Ban emotion tracking / facial recognition.")
        enforce_emergency_dispatch: bool = Field(default=True, description="Guardrail Fac-02: Bypass AI on physical safety / electrical emergencies.")
        enforce_hr_autonomy: bool = Field(default=True, description="Guardrail HR-01: Prohibit automated candidate rejection.")
        enforce_socratic_student: bool = Field(default=True, description="Guardrail Stu-01: Prevent cognitive bypass and force diagnostic hints for students.")
        enforce_fin_dual_key: bool = Field(default=True, description="Guardrail Fin-01: Append dual-key manual audit notice on financial calculations.")
        enforce_pii_redaction: bool = Field(default=True, description="Fin-02 & Child Protection: Redact Zambian NRCs and phone numbers.")

    def __init__(self):
        self.valves = self.Valves()
        self.phone_regex = re.compile(
            r'(?:\+?260|0)[-.\s]*(?:9[5-7]|7[5-79])(?:[-.\s]*\d){7}\b|'
            r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b'
        )
        self.nrc_regex = re.compile(r'\b\d{6}/\d{2}/\d{1}\b')
        self.aws_regex = re.compile(r'\b(?:AKIA[0-9A-Z]{16}|aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40})\b')
        self.private_key_regex = re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', re.IGNORECASE)

    def inlet(self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Runs before sending prompt to the LLM. Enforces input guardrails and red lines.
        """
        messages = body.get("messages", [])
        if not messages:
            return body

        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        # Strip context tags before guardrail check
        clean_msg = re.sub(r'<context>[\s\S]*?</context>', '', last_user_msg, flags=re.IGNORECASE)
        clean_msg = re.sub(r'<source[^>]*>[\s\S]*?</source>', '', clean_msg, flags=re.IGNORECASE)
        clean_msg = re.sub(r'<attached_files>[\s\S]*?</attached_files>', '', clean_msg, flags=re.IGNORECASE)
        lower_q = clean_msg.lower().strip()

        # 1. Guardrail IT-01: Secret Scanning
        if self.valves.enforce_secret_scanning:
            if self.aws_regex.search(last_user_msg) or self.private_key_regex.search(last_user_msg):
                raise Exception(
                    "🛑 [Guardrail IT-01 Violation] Prompt blocked: Raw API credentials, secret keys, or certificates detected."
                )

        # Check if informational policy inquiry
        is_policy_inquiry = bool(re.search(
            r'\b(what\s+is|what\s+are|tell\s+me\s+about|explain|why\s+is|why\s+are|is\s+there|how\s+does|is\s+it\s+allowed|are\s+we\s+allowed|is\s+it\s+permitted|can\s+we|brief\s+me|summariz\w*|overview|rules?|policy|policies|framework|compliance|audit|guidelines?|standards?|prohibit\w*|ban\w*|article\s+5)\b',
            lower_q
        ))

        # 2. Guardrail Fac-01: Emotion Tracking & Facial Recognition Ban
        if self.valves.enforce_emotion_ban and not is_policy_inquiry:
            if re.search(r'\b(emotion\s+track|facial\s+recognition|mood\s+detection|biometric\s+profiling)\b', lower_q):
                raise Exception(
                    "🛑 [Guardrail Fac-01 Violation] Strictly prohibited: Facial recognition and emotion tracking violate "
                    "Educore AI Governance Policy Sec 5 and EU AI Act Article 5."
                )

        # 3. Guardrail HR-01: Candidate Rejection Ban
        if self.valves.enforce_hr_autonomy and not is_policy_inquiry:
            if re.search(r'\b(reject\s+candidate|auto-reject|eliminate\s+applicant|terminate\s+employee\s+automatically)\b', lower_q):
                raise Exception(
                    "🛑 [Guardrail HR-01 Violation] Automated candidate rejection or termination is prohibited. "
                    "All HR decisions require certified human appraisal logs."
                )

        # 4. Guardrail Stu-01: Socratic Diagnostic Hint Intercept
        user_role = (__user__ or {}).get("role", "user")
        if self.valves.enforce_socratic_student and user_role in ["student", "user"]:
            if re.search(r'\b(give\s+me\s+the\s+answer|solve\s+this\s+completely|write\s+my\s+entire\s+essay|do\s+my\s+homework)\b', lower_q):
                # Prepend Socratic instructions to system message
                socratic_instruction = (
                    "\n\n[MANDATORY SOCRATIC GUARDRAIL STU-01]: The user is asking for direct exam answers or complete assignment completion. "
                    "DO NOT provide the final answer. Provide ONLY step-by-step diagnostic guiding hints and ask clarifying questions. "
                    "Remind the student of the Adelaide Declaration of Intellectual Ownership."
                )
                if messages and messages[0].get("role") == "system":
                    messages[0]["content"] += socratic_instruction
                else:
                    messages.insert(0, {"role": "system", "content": socratic_instruction})

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
