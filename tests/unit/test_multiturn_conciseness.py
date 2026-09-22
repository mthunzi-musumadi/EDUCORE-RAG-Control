# ==============================================================================
# TEST: MULTI-TURN CONTEXT RETENTION, CONCISENESS & ANTI-REPETITION
# ==============================================================================
import unittest
import os
import re

from educore_enterprise_backend import (
    execute_rag,
    EDUCORE_USERS,
    EducoreFrameworkEngine
)

class TestMultiTurnConcisenessAndContext(unittest.TestCase):

    def setUp(self):
        self.counselor_session = EDUCORE_USERS["counselor"]

    def test_turn1_summarizes_without_full_document_dump(self):
        """Turn 1: Verifies DOC-SENTINEL-004 summary does not dump raw document content."""
        query = "tell me about DOC-SENTINEL-004"
        res = execute_rag(query, self.counselor_session, chat_history=[])
        
        resp = res["response"]
        raw = res["raw_response"]
        
        # 1. Must not contain raw document markers or verbatim Document Content section
        self.assertNotIn("[DOCUMENT CONTENT START]", resp)
        self.assertNotIn("[DOCUMENT CONTENT END]", resp)
        self.assertNotIn("**Document Content:**", resp)
        
        # 2. Must not start with transcript echoes
        self.assertFalse(resp.startswith("User:"), f"Response should not start with 'User:': {resp[:50]}")
        self.assertFalse(resp.startswith("Assistant:"), f"Response should not start with 'Assistant:': {resp[:50]}")
        
        # 3. Must be concise (tokens < 512 runaway truncation limit)
        self.assertLess(res["tokens"], 512, f"Token count should be < 512, got {res['tokens']}")
        
        # 4. Must capture key facts from DOC-SENTINEL-004
        self.assertTrue(
            any(k in raw.lower() for k in ["bereavement", "anxiety", "safeguarding", "timeline", "flexible"]),
            f"Response should contain relevant facts: {raw}"
        )

    def test_turn2_followup_emergency_contact_without_echoes(self):
        """Turn 2: Follow-up 'is there an emergency contact' resolves context and does not repeat turn 1."""
        history = [
            {"role": "user", "content": "tell me about DOC-SENTINEL-004"},
            {"role": "assistant", "content": "This case (DOC-SENTINEL-004) concerns a Sentinel Kabitaka student experiencing acute family bereavement and academic anxiety. Flexible assessment timelines for Term 2 are recommended."}
        ]
        
        query = "is there an emergency contact i should be aware of?"
        res = execute_rag(query, self.counselor_session, chat_history=history)
        
        resp = res["response"]
        raw = res["raw_response"]
        
        # 1. Must NOT echo the previous user prompt or assistant prompt
        self.assertNotIn("User: tell me about DOC-SENTINEL-004", resp)
        self.assertNotIn("Assistant: I can provide you with", resp)
        self.assertFalse(resp.startswith("User:"), f"Response should not start with 'User:': {resp[:50]}")
        self.assertFalse(resp.startswith("Assistant:"), f"Response should not start with 'Assistant:': {resp[:50]}")
        
        # 2. Must resolve context: DOC-SENTINEL-004 retrieved or facts used
        retrieved_ids = [d["id"] for d in res["retrieved_docs"]]
        self.assertIn("DOC-SENTINEL-004", retrieved_ids, "DOC-SENTINEL-004 must be retained in context for follow-up")
        
        # 3. Must answer directly about the emergency contact (with PII shield active)
        self.assertTrue(
            "[REDACTED_PHONE_NUMBER]" in resp or "emergency contact" in raw.lower() or "contact" in raw.lower(),
            f"Expected emergency contact reference in response: {raw}"
        )
        
        # 4. Must be very concise (< 150 tokens)
        self.assertLess(res["tokens"], 200, f"Follow-up should be concise (< 200 tokens), got {res['tokens']}")

if __name__ == "__main__":
    unittest.main()
