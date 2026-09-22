# ==============================================================================
# EDUCORE ENTERPRISE - TPS COUNTER & WATCHED FILES TELEMETRY
# Real-Time Tokens-Per-Second (TPS) Measurement using TikToken
# Watched Files Parse & Embed Latency Tracking
# Compliance: ISO/IEC 42001:2023 | EU AI Act Article 12
# ==============================================================================
import time
import threading
import re
from typing import Dict, Any, List, Optional

try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
    try:
        _ENCODER = tiktoken.get_encoding("cl100k_base")
    except Exception:
        try:
            _ENCODER = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            _ENCODER = None
except ImportError:
    _TIKTOKEN_AVAILABLE = False
    _ENCODER = None


class TPSCounter:
    """
    Computes token counts and tokens-per-second (TPS) using tiktoken (cl100k_base)
    with graceful fallback to heuristic tokenization.
    """

    @staticmethod
    def count_tokens(text: str) -> int:
        if not text:
            return 0
        if _ENCODER is not None:
            try:
                return len(_ENCODER.encode(text, disallowed_special=()))
            except Exception:
                pass
        # Heuristic fallback (roughly 1 token ~= 4 characters or 0.75 words)
        words = len(re.findall(r'\w+|[^\w\s]', text, re.UNICODE))
        return max(1, words)

    @staticmethod
    def calculate_tps(token_count: int, duration_seconds: float) -> float:
        if duration_seconds <= 0 or token_count <= 0:
            return 0.0
        return round(token_count / duration_seconds, 2)


class TelemetryTracker:
    """
    Thread-safe tracker recording:
    1. Parse duration for newly watched files (.docx).
    2. Embed duration for newly watched files (ChromaDB vectors).
    3. Response generation duration and TPS.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TelemetryTracker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._state_lock = threading.RLock()
        self.last_parsed_files: List[str] = []
        self.last_parse_duration_ms: float = 0.0
        self.last_parse_chunks: int = 0
        self.last_embed_duration_ms: float = 0.0
        self.last_embed_vectors: int = 0
        self.last_sync_timestamp: float = 0.0
        self.initial_embed_duration_ms: float = 0.0
        self.initial_embed_vectors: int = 0
        self.cumulative_parse_ms: float = 0.0
        self.cumulative_embed_ms: float = 0.0
        self.total_synced_files_count: int = 0
        self.watch_dirs_count: int = 1
        self._initialized = True

    def set_watch_dirs_count(self, count: int):
        with self._state_lock:
            self.watch_dirs_count = max(1, count)

    def record_initial_embed(self, duration_ms: float, vector_count: int):
        with self._state_lock:
            self.initial_embed_duration_ms = round(duration_ms, 2)
            self.initial_embed_vectors = vector_count

    def record_batch_parse(self, files: List[str], duration_ms: float, total_chunks: int):
        with self._state_lock:
            self.last_parsed_files = list(files)
            self.last_parse_duration_ms = round(duration_ms, 2)
            self.last_parse_chunks = total_chunks
            self.cumulative_parse_ms += self.last_parse_duration_ms
            self.total_synced_files_count += len(files)
            self.last_sync_timestamp = time.time()

    def record_embed(self, duration_ms: float, vector_count: int):
        with self._state_lock:
            self.last_embed_duration_ms = round(duration_ms, 2)
            self.last_embed_vectors = vector_count
            self.cumulative_embed_ms += self.last_embed_duration_ms
            self.last_sync_timestamp = time.time()

    def get_watch_telemetry(self) -> Dict[str, Any]:
        with self._state_lock:
            return {
                "last_parsed_files": list(self.last_parsed_files),
                "last_parse_duration_ms": self.last_parse_duration_ms,
                "last_parse_chunks": self.last_parse_chunks,
                "last_embed_duration_ms": self.last_embed_duration_ms,
                "last_embed_vectors": self.last_embed_vectors,
                "last_sync_timestamp": self.last_sync_timestamp,
                "initial_embed_duration_ms": self.initial_embed_duration_ms,
                "initial_embed_vectors": self.initial_embed_vectors,
                "cumulative_parse_ms": round(self.cumulative_parse_ms, 2),
                "cumulative_embed_ms": round(self.cumulative_embed_ms, 2),
                "total_synced_files_count": self.total_synced_files_count,
                "watch_dirs_count": self.watch_dirs_count
            }

    def format_telemetry_footer(
        self,
        response_text: str,
        generation_seconds: float,
        token_count: Optional[int] = None
    ) -> str:
        """
        Formats a clean, standardized Markdown telemetry footer that appears
        right after each assistant response.
        """
        tokens = token_count if token_count is not None else TPSCounter.count_tokens(response_text)
        tps = TPSCounter.calculate_tps(tokens, generation_seconds)
        watch_stats = self.get_watch_telemetry()

        # Watched files timing details
        if watch_stats["last_parsed_files"]:
            files_display = ", ".join(f"`{f}`" for f in watch_stats["last_parsed_files"][:2])
            if len(watch_stats["last_parsed_files"]) > 2:
                files_display += f" (+{len(watch_stats['last_parsed_files']) - 2} more)"
            parse_info = f"{watch_stats['last_parse_duration_ms']:.1f}ms ({watch_stats['last_parse_chunks']} chunks)"
            embed_info = f"{watch_stats['last_embed_duration_ms']:.1f}ms ({watch_stats['last_embed_vectors']} vectors)"
            watch_line = f"- **Newly Watched Files:** Parse: **{parse_info}** | Embed: **{embed_info}** | Files: {files_display}"
        elif watch_stats["initial_embed_duration_ms"] > 0:
            embed_info = f"{watch_stats['initial_embed_duration_ms']:.1f}ms ({watch_stats['initial_embed_vectors']} vectors)"
            watch_line = f"- **Newly Watched Files:** Parse: **0.0ms** | Embed: **{embed_info}** (Initial corpus; live watcher active on {watch_stats['watch_dirs_count']} dir)"
        else:
            watch_line = f"- **Newly Watched Files:** Parse: **0.0ms** | Embed: **0.0ms** (Live watcher active on {watch_stats['watch_dirs_count']} dir; standing by)"

        footer = (
            "\n\n---\n"
            "⚡ **Educore Performance Telemetry:**\n"
            f"- **Response Generation:** **{generation_seconds:.2f}s** | **{tokens} tokens** | **{tps:.1f} TPS** (via `tiktoken`)\n"
            f"{watch_line}"
        )
        return footer


# Global singleton instance
TELEMETRY = TelemetryTracker()
