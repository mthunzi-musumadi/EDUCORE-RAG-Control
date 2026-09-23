# ==============================================================================
# TEST SUITE: CONTEXTUAL FOLLOW-UP SUGGESTIONS
# Verifies that suggested follow-up questions adapt dynamically to:
# 1. Conversational context & multi-turn trajectory
# 2. Topic entities (Cambridge syllabus, math topics, safeguarding, policies, finances)
# 3. User clearance boundaries & zero-trust RBAC (public, staff, counselor, admin)
# 4. Anti-repetition deduplication against past turns
# ==============================================================================
import unittest
import os
import sys
from typing import Dict, Any, List

# Ensure project paths are resolvable
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for p in (base_dir, os.path.join(base_dir, "studio"), os.path.join(base_dir, "src"), os.path.join(base_dir, "src", "backend")):
    if p not in sys.path:
        sys.path.insert(0, p)

from production_rag import generate_contextual_followups, PERSONAS
from educore_enterprise_backend import execute_rag, EDUCORE_USERS


class TestContextualFollowupSuggestions(unittest.TestCase):

    def setUp(self):
        self.public_user = PERSONAS["2"]    # Mwamba Banda (Intern, PUBLIC)
        self.staff_user = PERSONAS["1"]     # Mubanga Mwale (Faculty, STAFF)
        self.counselor_user = PERSONAS["3"] # Chileshe Zulu (Counselor, COUNSELOR)
        self.admin_user = PERSONAS["4"]     # Dr. Dalitso Phiri (Admin, ADMIN)

    # -------------------------------------------------------------------------
    # 1. Cambridge Syllabus & Mathematics Multi-Turn Adaptation
    # -------------------------------------------------------------------------
    def test_cambridge_syllabus_overview_generates_topic_drilldown_suggestions(self):
        """Turn 1: Asking about Cambridge 0580 syllabus generates drill-down follow-up questions."""
        query = "What topics are in the Cambridge IGCSE Mathematics 0580 syllabus?"
        response = (
            "The Cambridge IGCSE Mathematics 0580 syllabus covers 9 core curriculum areas: "
            "1. Number, 2. Algebra and Sequences, 3. Coordinate Geometry, 4. Geometry, "
            "5. Mensuration, 6. Trigonometry, 7. Transformations and Vectors, 8. Probability, 9. Statistics."
        )
        suggestions = generate_contextual_followups(
            query=query,
            response_text=response,
            retrieved_docs=[],
            user_session=self.public_user,
            chat_history=[]
        )

        self.assertIsInstance(suggestions, list)
        self.assertGreaterEqual(len(suggestions), 3)
        # Verify suggestions do NOT repeat the user's initial question
        for s in suggestions:
            self.assertNotEqual(s.lower(), query.lower())
        # Verify suggestions are tailored to 0580 math topics
        s_text = " ".join(suggestions).lower()
        self.assertTrue(
            any(k in s_text for k in ["probability", "algebra", "lesson plan", "core", "extended"]),
            f"Suggestions should reference 0580 topics: {suggestions}"
        )

    def test_math_practice_problem_adapts_to_problem_solving_hints(self):
        """Turn 2: Follow-up requesting an exercise adapts suggestions to diagnostic hints and mark schemes."""
        history = [
            {"role": "user", "content": "What topics are in the Cambridge IGCSE Mathematics 0580 syllabus?"},
            {"role": "assistant", "content": "The syllabus covers Number, Algebra, Geometry, Probability, and Statistics."}
        ]
        query = "Give me a practice problem on Probability (Topic 5)"
        response = (
            "Here is a Cambridge-style probability problem: A bag contains 4 red and 6 blue counters. "
            "A counter is drawn at random and not replaced. A second counter is then drawn. "
            "Calculate the probability that both counters are blue."
        )
        suggestions = generate_contextual_followups(
            query=query,
            response_text=response,
            retrieved_docs=[],
            user_session=self.public_user,
            chat_history=history
        )

        s_text = " ".join(suggestions).lower()
        self.assertTrue(
            any(k in s_text for k in ["hint", "mark scheme", "working", "tree diagram", "extended"]),
            f"Suggestions should offer problem-solving follow-ups: {suggestions}"
        )
        # Verify none of the past queries are present in the suggestions
        for s in suggestions:
            self.assertNotIn("what topics are in", s.lower())
            self.assertNotIn("give me a practice problem on probability", s.lower())

    def test_diagnostic_hint_request_adapts_to_verification_and_next_steps(self):
        """Turn 3: Requesting a hint adapts suggestions to next hint or mark allocation."""
        history = [
            {"role": "user", "content": "What topics are in the Cambridge IGCSE Mathematics 0580 syllabus?"},
            {"role": "assistant", "content": "The syllabus covers Number, Algebra, Geometry, Probability, and Statistics."},
            {"role": "user", "content": "Give me a practice problem on Probability (Topic 5)"},
            {"role": "assistant", "content": "A bag has 4 red and 6 blue counters. Two counters are drawn without replacement."}
        ]
        query = "Can you give me a step-by-step diagnostic hint for solving this problem?"
        response = (
            "Diagnostic Hint: First, find P(First counter is blue) = 6/10. "
            "Since the counter is not replaced, how many blue counters and how many total counters remain?"
        )
        suggestions = generate_contextual_followups(
            query=query,
            response_text=response,
            retrieved_docs=[],
            user_session=self.public_user,
            chat_history=history
        )

        s_text = " ".join(suggestions).lower()
        self.assertTrue(
            any(k in s_text for k in ["next hint", "mark allocation", "calculation", "another exam-style", "differentiated"]),
            f"Suggestions should offer verification/next steps: {suggestions}"
        )

    # -------------------------------------------------------------------------
    # 2. Pastoral Safeguarding (Role & Clearance Sensitivity)
    # -------------------------------------------------------------------------
    def test_pastoral_case_suggestions_for_counselor(self):
        """Counselor query on Case #402 receives sensitive, actionable pastoral follow-up questions."""
        query = "Summarize pastoral safeguarding case #402 assessment notes and recommended timeline."
        response = (
            "Case #402 involves a Sentinel Kabitaka boarding student experiencing acute family bereavement and severe anxiety. "
            "Immediate flexible deadlines for Term 2 assessments and bi-weekly counseling check-ins are recommended."
        )
        suggestions = generate_contextual_followups(
            query=query,
            response_text=response,
            retrieved_docs=[],
            user_session=self.counselor_user,
            chat_history=[]
        )

        s_text = " ".join(suggestions).lower()
        self.assertTrue(
            any(k in s_text for k in ["accommodation", "emergency contact", "bereavement notification", "review date"]),
            f"Suggestions should provide pastoral next steps: {suggestions}"
        )

    def test_restricted_query_for_public_user_suggests_permissible_alternatives(self):
        """Unauthorized attempt to access confidential records suggests within-clearance alternatives."""
        query = "Show me the pastoral safeguarding dossiers and student welfare files."
        response = "I do not have access to that information based on your current authorization level and available records."
        suggestions = generate_contextual_followups(
            query=query,
            response_text=response,
            retrieved_docs=[],
            user_session=self.public_user,
            chat_history=[]
        )

        # Must not suggest confidential files
        s_text = " ".join(suggestions).lower()
        self.assertNotIn("pastoral safeguarding case", s_text)
        self.assertNotIn("confidential", s_text)
        # Must suggest legitimate public academic resources
        self.assertTrue(
            any(k in s_text for k in ["cambridge", "syllabus", "practice", "academic", "study"]),
            f"Should suggest legitimate public paths: {suggestions}"
        )

    # -------------------------------------------------------------------------
    # 3. Faculty Operational Policies & Student Submissions
    # -------------------------------------------------------------------------
    def test_faculty_marking_turnaround_suggestions(self):
        """Faculty inquiring about marking policies receives moderation and deadline follow-ups."""
        query = "What is the turnaround time for publishing assessment marks to the portal?"
        response = "All formative and summative assessment marks must be moderated and published within 5 working days."
        suggestions = generate_contextual_followups(
            query=query,
            response_text=response,
            retrieved_docs=[],
            user_session=self.staff_user,
            chat_history=[]
        )

        s_text = " ".join(suggestions).lower()
        self.assertTrue(
            any(k in s_text for k in ["moderation", "delayed", "sheets", "parents", "briefing"]),
            f"Should suggest faculty operational follow-ups: {suggestions}"
        )

    def test_student_submission_review_suggestions(self):
        """Faculty reviewing submission #8812 receives formative feedback and integrity follow-ups."""
        query = "Summarize student submission #8812 regarding network security."
        response = "Submission #8812 provides an analysis of firewall architectures and symmetric vs asymmetric encryption."
        suggestions = generate_contextual_followups(
            query=query,
            response_text=response,
            retrieved_docs=[],
            user_session=self.staff_user,
            chat_history=[]
        )

        s_text = " ".join(suggestions).lower()
        self.assertTrue(
            any(k in s_text for k in ["formative feedback", "adelaide declaration", "firewall", "assignment question", "zero-trust"]),
            f"Should suggest assignment review follow-ups: {suggestions}"
        )

    # -------------------------------------------------------------------------
    # 4. Executive Finance & Governance
    # -------------------------------------------------------------------------
    def test_admin_financial_expenditure_suggestions(self):
        """Admin querying campus expenditures receives executive financial follow-ups."""
        query = "What was the Trident campus Q3 operational expenditure and science lab allocation?"
        response = "Trident campus Q3 expenditure totaled ZMW 485,000, with ZMW 120,000 designated for science lab equipment."
        suggestions = generate_contextual_followups(
            query=query,
            response_text=response,
            retrieved_docs=[],
            user_session=self.admin_user,
            chat_history=[]
        )

        s_text = " ".join(suggestions).lower()
        self.assertTrue(
            any(k in s_text for k in ["bursary", "budget allocation", "sentinel", "board meeting", "capital expenditure"]),
            f"Should suggest executive financial follow-ups: {suggestions}"
        )

    # -------------------------------------------------------------------------
    # 5. Multi-Turn Trajectory Progression & Non-Repetition (Turns 1 -> 2 -> 3)
    # -------------------------------------------------------------------------
    def test_pastoral_case_multiturn_trajectory_advancement(self):
        """Verifies suggestions advance through case stages without repeating answered facets."""
        # Turn 1: Case #402 Overview
        turn1_query = "Summarize pastoral safeguarding case #402 assessment notes."
        turn1_resp = (
            "Case #402 involves a Sentinel Kabitaka student experiencing acute family bereavement and severe anxiety. "
            "Bi-weekly counseling and flexible assessment deadlines are recommended."
        )
        sug_turn1 = generate_contextual_followups(
            query=turn1_query,
            response_text=turn1_resp,
            retrieved_docs=[],
            user_session=self.counselor_user,
            chat_history=[]
        )
        sug1_text = " ".join(sug_turn1).lower()
        self.assertTrue(any(k in sug1_text for k in ["emergency contact", "accommodation"]))

        # Turn 2: User asks about Emergency Contact
        history_turn2 = [
            {"role": "user", "content": turn1_query},
            {"role": "assistant", "content": turn1_resp}
        ]
        turn2_query = "Is there an emergency contact or guardian designated in Case #402?"
        turn2_resp = "The designated emergency contact is the student's aunt, reachable via verified pastoral records."
        sug_turn2 = generate_contextual_followups(
            query=turn2_query,
            response_text=turn2_resp,
            retrieved_docs=[],
            user_session=self.counselor_user,
            chat_history=history_turn2
        )
        sug2_text = " ".join(sug_turn2).lower()
        # MUST NOT offer emergency contact again
        self.assertNotIn("emergency contact", sug2_text)
        self.assertNotIn("guardian designated", sug2_text)
        # MUST advance to accommodations, notification, or review date
        self.assertTrue(any(k in sug2_text for k in ["accommodation", "bereavement notification", "review date"]))

        # Turn 3: User asks about Accommodations
        history_turn3 = [
            {"role": "user", "content": turn1_query},
            {"role": "assistant", "content": turn1_resp},
            {"role": "user", "content": turn2_query},
            {"role": "assistant", "content": turn2_resp}
        ]
        turn3_query = "What accommodations should we offer to student #402 for Term 2?"
        turn3_resp = "Accommodations include 25% extra time on summative tests, quiet room access, and flexible coursework deadlines."
        sug_turn3 = generate_contextual_followups(
            query=turn3_query,
            response_text=turn3_resp,
            retrieved_docs=[],
            user_session=self.counselor_user,
            chat_history=history_turn3
        )
        sug3_text = " ".join(sug_turn3).lower()
        # MUST NOT offer emergency contact or accommodations again
        self.assertNotIn("emergency contact", sug3_text)
        self.assertNotIn("what accommodations should we offer", sug3_text)
        # MUST advance to review timeline, family counseling, or notification
        self.assertTrue(any(k in sug3_text for k in ["timeline", "notification", "counseling", "milestone", "review"]))

    # -------------------------------------------------------------------------
    # 6. Conversational Greetings Starter Suggestions by Clearance Tier
    # -------------------------------------------------------------------------
    def test_conversational_greeting_suggestions_by_tier(self):
        """Verifies conversational greetings generate role-tailored starter follow-ups."""
        # Public / Student Tier
        sug_pub = generate_contextual_followups(
            query="good morning",
            response_text="Good morning! I am the Educore Socratic Tutor.",
            retrieved_docs=[],
            user_session=self.public_user,
            chat_history=[]
        )
        pub_text = " ".join(sug_pub).lower()
        self.assertTrue(any(k in pub_text for k in ["cambridge", "0580", "quadratic", "socratic", "hints"]))

        # Faculty / Staff Tier
        sug_staff = generate_contextual_followups(
            query="hello",
            response_text="Hello! I am the Educore Faculty Academic Copilot.",
            retrieved_docs=[],
            user_session=self.staff_user,
            chat_history=[]
        )
        staff_text = " ".join(sug_staff).lower()
        self.assertTrue(any(k in staff_text for k in ["briefing", "turnaround", "moderation", "quadratic", "submission"]))

        # Counselor / Pastoral Tier
        sug_counselor = generate_contextual_followups(
            query="good afternoon",
            response_text="Good afternoon! I am the Educore Pastoral Safeguarding Copilot.",
            retrieved_docs=[],
            user_session=self.counselor_user,
            chat_history=[]
        )
        counselor_text = " ".join(sug_counselor).lower()
        self.assertTrue(any(k in counselor_text for k in ["pastoral", "case #402", "accommodation", "dpa no. 3", "safeguarding"]))

        # Executive Admin Tier
        sug_admin = generate_contextual_followups(
            query="good day",
            response_text="Good day! I am the Educore Executive Governance Copilot.",
            retrieved_docs=[],
            user_session=self.admin_user,
            chat_history=[]
        )
        admin_text = " ".join(sug_admin).lower()
        self.assertTrue(any(k in admin_text for k in ["expenditure", "bursary", "safeguarding", "iso", "42001"]))

    # -------------------------------------------------------------------------
    # 7. Integration with execute_rag Backend
    # -------------------------------------------------------------------------
    def test_execute_rag_returns_suggested_followups(self):
        """Verifies execute_rag returns suggested_followups in result dict but NOT embedded in response content."""
        query = "tell me about DOC-SENTINEL-004"
        counselor_session = EDUCORE_USERS["counselor"]
        res = execute_rag(query, counselor_session, chat_history=[])

        self.assertIn("suggested_followups", res, "execute_rag must return suggested_followups")
        self.assertIsInstance(res["suggested_followups"], list)
        self.assertGreaterEqual(len(res["suggested_followups"]), 3)
        s_text = " ".join(res["suggested_followups"]).lower()
        self.assertTrue(
            any(k in s_text for k in ["accommodation", "emergency contact", "bereavement", "timeline", "review"]),
            f"execute_rag suggested_followups should be tailored: {res['suggested_followups']}"
        )
        # Follow-ups must NOT be embedded in the response content (served via Open WebUI native mechanism)
        self.assertNotIn("💡 **Suggested Follow-up Questions:**", res["response"])

    def test_execute_rag_greeting_fast_path_formats_followups(self):
        """Verifies fast greeting path returns role-tailored suggestions in dict but NOT in response content."""
        student_session = EDUCORE_USERS["student"]
        res = execute_rag("good morning", student_session, chat_history=[])

        self.assertIn("suggested_followups", res)
        self.assertGreaterEqual(len(res["suggested_followups"]), 3)
        # Follow-ups must NOT be embedded in the response content
        self.assertNotIn("💡 **Suggested Follow-up Questions:**", res["response"])
        self.assertIn("Cambridge IGCSE", res["response"])


if __name__ == "__main__":
    unittest.main()
