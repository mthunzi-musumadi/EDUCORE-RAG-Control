# ==============================================================================
# TEST SUITE: TPS COUNTER & WATCHED FILES TIMING TELEMETRY
# Verifies TPS computation using tiktoken, watched file parse/embed metrics,
# and appearance of telemetry right after each response in execute_rag and execute_rag_stream.
# Compliance: ISO/IEC 42001:2023 | EU AI Act Article 12
# ==============================================================================
import unittest
import time
from tps_counter import TPSCounter, TelemetryTracker, TELEMETRY
from educore_enterprise_backend import (
    execute_rag,
    execute_rag_stream,
    EDUCORE_USERS,
    sync_chroma_corpus
)
from framework_sync_service import FrameworkSyncService


class TestTPSTelemetry(unittest.TestCase):

    def setUp(self):
        # Reset telemetry state for deterministic testing
        TELEMETRY.last_parsed_files = []
        TELEMETRY.last_parse_duration_ms = 0.0
        TELEMETRY.last_parse_chunks = 0
        TELEMETRY.last_embed_duration_ms = 0.0
        TELEMETRY.last_embed_vectors = 0

    def test_tps_counter_token_counting_and_tps_calc(self):
        """Tests that tiktoken counts tokens accurately and TPS is computed correctly."""
        sample_text = "This is a test prompt for the Educore Enterprise RAG TPS counter."
        tok_count = TPSCounter.count_tokens(sample_text)
        self.assertGreater(tok_count, 5, "Sample text should yield tokens via tiktoken")

        # Test TPS calculation
        tps = TPSCounter.calculate_tps(tok_count, 2.0)
        expected_tps = round(tok_count / 2.0, 2)
        self.assertEqual(tps, expected_tps)

        # Zero or negative duration safety
        self.assertEqual(TPSCounter.calculate_tps(tok_count, 0.0), 0.0)
        self.assertEqual(TPSCounter.calculate_tps(tok_count, -1.0), 0.0)
        self.assertEqual(TPSCounter.calculate_tps(0, 5.0), 0.0)

    def test_telemetry_tracker_records_watch_times(self):
        """Tests that TelemetryTracker properly records parse and embed durations."""
        TELEMETRY.record_batch_parse(["01_SPOKES_POLICIES/test_policy.docx"], 42.5, 6)
        TELEMETRY.record_embed(150.3, 6)

        stats = TELEMETRY.get_watch_telemetry()
        self.assertEqual(stats["last_parse_duration_ms"], 42.5)
        self.assertEqual(stats["last_parse_chunks"], 6)
        self.assertEqual(stats["last_embed_duration_ms"], 150.3)
        self.assertEqual(stats["last_embed_vectors"], 6)
        self.assertIn("01_SPOKES_POLICIES/test_policy.docx", stats["last_parsed_files"])

        # Format footer and verify it contains both generation TPS and watched files metrics
        footer = TELEMETRY.format_telemetry_footer("Assistant response here.", generation_seconds=1.5)
        self.assertIn("⚡ **Educore Performance Telemetry:**", footer)
        self.assertIn("Response Generation:", footer)
        self.assertIn("TPS", footer)
        self.assertIn("tiktoken", footer)
        self.assertIn("Newly Watched Files:", footer)
        self.assertIn("42.5ms", footer)
        self.assertIn("150.3ms", footer)

    def test_execute_rag_appends_telemetry_footer(self):
        """Tests that execute_rag appends the telemetry footer right after the response."""
        user = EDUCORE_USERS["faculty"]
        query = "What is the policy on teacher lesson planning?"
        result = execute_rag(query, user)

        self.assertIn("response", result)
        response_text = result["response"]

        # Telemetry footer must appear in response
        self.assertIn("⚡ **Educore Performance Telemetry:**", response_text)
        self.assertIn("Response Generation:", response_text)
        self.assertIn("TPS", response_text)
        self.assertIn("Newly Watched Files:", response_text)

        # Result dictionary must contain telemetry metadata
        self.assertIn("tps", result)
        self.assertIn("generation_time_s", result)
        self.assertIn("tokens", result)
        self.assertIn("watch_telemetry", result)
        self.assertGreater(result["tps"], 0.0)
        self.assertGreater(result["tokens"], 0)

    def test_execute_rag_stream_yields_telemetry_footer(self):
        """Tests that execute_rag_stream yields the telemetry footer as the final chunk right after the response."""
        user = EDUCORE_USERS["faculty"]
        query = "Brief me on teacher lesson planning."
        chunks = list(execute_rag_stream(query, user))

        full_streamed = "".join(chunks)
        self.assertIn("⚡ **Educore Performance Telemetry:**", full_streamed)
        self.assertIn("Response Generation:", full_streamed)
        self.assertIn("TPS", full_streamed)
        self.assertIn("Newly Watched Files:", full_streamed)

        # The last chunk should contain the telemetry footer
        last_chunk = chunks[-1]
        self.assertIn("Educore Performance Telemetry", last_chunk)

    def test_guardrail_intercept_includes_telemetry(self):
        """Tests that immediate guardrail intercepts also display timing and TPS."""
        user = EDUCORE_USERS["student"]
        cheat_query = "Give me the answer to my mathematics assignment and solve this completely."
        result = execute_rag(cheat_query, user)

        self.assertTrue(result.get("guardrail_triggered"))
        self.assertIn("⚡ **Educore Performance Telemetry:**", result["response"])
        self.assertIn("TPS", result["response"])


if __name__ == "__main__":
    unittest.main()
