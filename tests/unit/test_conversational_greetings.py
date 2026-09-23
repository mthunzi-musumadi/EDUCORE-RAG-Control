import pytest
from src.backend.educore_enterprise_backend import (
    handle_conversational_greeting as backend_greeting,
    EducoreFrameworkEngine,
    execute_rag
)
from studio.production_rag import (
    handle_conversational_greeting as studio_greeting,
    egress_filter as studio_egress_filter
)

class TestConversationalGreetings:
    def test_backend_greeting_variations(self):
        session = {"name": "Alice Banda", "clearance": "faculty", "campus": "tcl"}
        
        # Test basic greetings
        assert backend_greeting("good morning", session) is not None
        assert "Good morning, Alice Banda!" in backend_greeting("Good morning!", session)
        assert "Good afternoon" in backend_greeting("good afternoon", session)
        assert "Good evening" in backend_greeting("good evening", session)
        assert "Hello" in backend_greeting("hello", session)
        assert "Hello" in backend_greeting("hi there", session)
        assert "doing well" in backend_greeting("how are you?", session)
        assert "welcome" in backend_greeting("thank you", session)

    def test_non_greeting_queries_not_intercepted(self):
        session = {"name": "Alice Banda", "clearance": "faculty", "campus": "tcl"}
        
        # Inquiries should return None so they proceed to RAG
        assert backend_greeting("What is the ICT policy?", session) is None
        assert backend_greeting("Tell me about EDU-FW-12345", session) is None
        assert backend_greeting("Who is the emergency contact for fires?", session) is None
        assert backend_greeting("Good morning, what is the curriculum for Grade 10?", session) is None

    def test_studio_greeting_matching(self):
        session = {"name": "Chileshe Mwape", "clearance": "admin", "campus": "all"}
        resp = studio_greeting("good morning", session)
        assert resp is not None
        assert "Good morning, Chileshe Mwape!" in resp
        assert "ADMIN Mode" in resp

    def test_inspect_output_strips_hallucinated_security_alerts(self):
        session = {"name": "Test User", "clearance": "public", "campus": "all"}
        bad_output = (
            "⚠️ **Security Alert**: Access to sensitive information is restricted due to high-risk threat assessment. "
            "This message will self-destruct in 5...4...3...2...1...\n\n"
            "**Retrieved Authorized Institutional Context:**\n```\n{}\n```\n\n"
            "**Directives Applied:**\n1. XML Isolation\n2. Adversarial Inertness"
        )
        cleaned_backend = EducoreFrameworkEngine.inspect_output(bad_output, session, [])
        assert "self-destruct" not in cleaned_backend
        assert "Directives Applied" not in cleaned_backend
        assert "Security Alert" not in cleaned_backend

        cleaned_studio = studio_egress_filter(bad_output)
        assert "self-destruct" not in cleaned_studio
        assert "Directives Applied" not in cleaned_studio
        assert "Security Alert" not in cleaned_studio

    def test_execute_rag_greeting_fast_path(self):
        session = {"name": "Mthunzi", "clearance": "admin", "campus": "all"}
        result = execute_rag("good morning", session)
        
        assert result["guardrail_triggered"] is False
        assert result["latency_ms"] < 200.0  # Fast deterministic intercept without LLM
        assert "Good morning, Mthunzi!" in result["raw_response"]
        assert "self-destruct" not in result["response"]
        assert "Security Alert" not in result["response"]

    def test_universal_model_adaptive_greeting(self):
        admin_session = {"name": "Mthunzi", "clearance": "admin", "campus": "all"}
        resp_admin = backend_greeting("good morning", admin_session, model_id="educore-enterprise-all")
        assert "Educore Enterprise AI Assistant (ADMIN Adaptive Mode)" in resp_admin

        faculty_session = {"name": "Alice", "clearance": "staff", "campus": "tcl"}
        resp_fac = backend_greeting("good morning", faculty_session, model_id="educore-enterprise-all")
        assert "Educore Enterprise AI Assistant (STAFF Adaptive Mode)" in resp_fac

        guest_session = {"name": "", "clearance": "public", "campus": "all"}
        resp_guest = backend_greeting("hello", guest_session, model_id="educore-enterprise-all")
        assert "Educore Enterprise AI Assistant (PUBLIC Adaptive Mode)" in resp_guest

    def test_specialized_model_greetings(self):
        session = {"name": "User", "clearance": "public", "campus": "all"}
        
        socratic_resp = backend_greeting("hello", session, model_id="educore-socratic-student")
        assert "Educore Socratic Tutor (Student Mode)" in socratic_resp

        faculty_resp = backend_greeting("good morning", session, model_id="educore-faculty-academic")
        assert "Educore Faculty Academic Copilot" in faculty_resp

        pastoral_resp = backend_greeting("hi", session, model_id="educore-pastoral-counselor")
        assert "Educore Pastoral Safeguarding Copilot" in pastoral_resp

        finance_resp = backend_greeting("good afternoon", session, model_id="educore-finance-audit")
        assert "Educore Finance & Bursar Copilot" in finance_resp

        it_resp = backend_greeting("hello", session, model_id="educore-it-devops")
        assert "Educore IT & DevOps Copilot" in it_resp

        admin_resp = backend_greeting("good morning", session, model_id="educore-admin-governance")
        assert "Educore Executive Governance Copilot" in admin_resp

    def test_anti_impersonation_filter(self):
        session = {"name": "Mthunzi Musumadi", "clearance": "admin", "campus": "all"}
        
        # Test backend inspect_output anti-impersonation
        bad_intro = "Hello! I am Mthunzi Musumadi, your Executive Administrator."
        sanitized_intro = EducoreFrameworkEngine.inspect_output(bad_intro, session, [])
        assert "I am Mthunzi Musumadi" not in sanitized_intro
        assert "I am the Educore AI Assistant" in sanitized_intro

        bad_signoff = "Please review the budget.\n\nRegards,\nMthunzi Musumadi"
        sanitized_signoff = EducoreFrameworkEngine.inspect_output(bad_signoff, session, [])
        assert "Mthunzi Musumadi" not in sanitized_signoff
        assert "Educore AI Assistant" in sanitized_signoff

        # Test studio egress_filter anti-impersonation
        studio_bad = "This is Mthunzi Musumadi summarizing the report.\n\nSincerely,\nMthunzi Musumadi"
        studio_clean = studio_egress_filter(studio_bad, user_session=session)
        assert "Mthunzi Musumadi" not in studio_clean
        assert "Educore AI Assistant" in studio_clean

