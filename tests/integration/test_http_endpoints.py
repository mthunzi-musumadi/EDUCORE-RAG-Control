# ==============================================================================
# TEST SUITE: HTTP / OPENAI API ENDPOINTS FOR OPEN WEBUI
# Verifies GET /v1/models, POST /v1/chat/completions (JSON & Stream), /health, /api/tags
# ==============================================================================
import urllib.request
import urllib.error
import json
import time
import subprocess
import sys
import os

TEST_PORT = 8001
SERVER_PROC = None

def start_test_server():
    global SERVER_PROC
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    python_exe = os.path.join(project_root, "framework_control", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable
    script = os.path.join(project_root, "src", "backend", "educore_enterprise_backend.py")
    env = os.environ.copy()
    env.setdefault("EDUCORE_TEST_MODE", "1")
    env.setdefault("EDUCORE_AUDIT_LOG_PATH", os.path.join(project_root, "data", "logs", "test_aims_rag_audit.jsonl"))
    SERVER_PROC = subprocess.Popen([python_exe, script, str(TEST_PORT)], env=env)
    # Wait for server to bind (give up to 60s for ChromaDB and model loading)
    for _ in range(60):
        time.sleep(1.0)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{TEST_PORT}/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
    return False

def stop_test_server():
    global SERVER_PROC
    if SERVER_PROC:
        SERVER_PROC.terminate()
        try:
            SERVER_PROC.wait(timeout=3)
        except Exception:
            SERVER_PROC.kill()

def setup_module(module):
    if not start_test_server():
        raise RuntimeError(f"Failed to start test server on port {TEST_PORT}")

def teardown_module(module):
    stop_test_server()

def test_endpoints():
    base_url = f"http://127.0.0.1:{TEST_PORT}"
    print(f"Testing Educore Governance API on {base_url}...")

    # 1. Test /health
    with urllib.request.urlopen(f"{base_url}/health") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "online"
        print("  [PASS] GET /health")

    # 2. Test /v1/models
    with urllib.request.urlopen(f"{base_url}/v1/models") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        model_ids = [m["id"] for m in data["data"]]
        assert "educore-enterprise-all" in model_ids
        assert "educore-socratic-student" in model_ids
        assert "educore-faculty-academic" in model_ids
        assert "educore-pastoral-counselor" in model_ids
        assert "educore-finance-audit" in model_ids
        print(f"  [PASS] GET /v1/models ({len(model_ids)} models available)")

    # 3. Test /api/tags (Ollama format)
    with urllib.request.urlopen(f"{base_url}/api/tags") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "models" in data
        print("  [PASS] GET /api/tags (Ollama Compatibility)")

    # 4. Test POST /v1/chat/completions (Non-streaming JSON)
    req_payload = {
        "model": "educore-socratic-student",
        "messages": [
            {"role": "user", "content": "What is quadratic equation formula in IGCSE Mathematics 0580?"}
        ],
        "stream": False
    }
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(req_payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Educore-User": "student"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "choices" in data
        content = data["choices"][0]["message"]["content"]
        assert len(content) > 10
        print(f"  [PASS] POST /v1/chat/completions (Response length: {len(content)} chars)")

    # 5. Test POST /v1/chat/completions (Streaming SSE)
    stream_payload = {
        "model": "educore-faculty-academic",
        "messages": [
            {"role": "user", "content": "Give a brief overview of the Cambridge IGCSE Math syllabus."}
        ],
        "stream": True
    }
    stream_req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(stream_payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Educore-User": "faculty"}
    )
    with urllib.request.urlopen(stream_req, timeout=60) as resp:
        assert resp.status == 200
        assert "text/event-stream" in resp.headers.get("Content-Type", "")
        chunks = []
        for line in resp:
            line_str = line.decode("utf-8").strip()
            if line_str.startswith("data: ") and line_str != "data: [DONE]":
                chunk_json = json.loads(line_str[6:])
                delta = chunk_json["choices"][0]["delta"].get("content", "")
                chunks.append(delta)
        full_streamed = "".join(chunks)
        assert len(full_streamed) > 10
        print(f"  [PASS] POST /v1/chat/completions (Streamed {len(chunks)} chunks, {len(full_streamed)} chars)")

    print("\nALL HTTP & OPENAI API ENDPOINTS VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        print("Starting test server...")
        if not start_test_server():
            print("Failed to start server!")
            sys.exit(1)
        test_endpoints()
    finally:
        print("Stopping test server...")
        stop_test_server()
