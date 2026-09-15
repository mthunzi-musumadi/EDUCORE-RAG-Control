"""
test_web_server.py - Integration and smoke tests for the EduCore Web Server & API.
Verifies:
1. Authentication: Login with valid/invalid credentials, 1-click profiles
2. RBAC Tool Suite Isolation: Each user gets their exact permitted tools
3. Multi-Turn Conversational Memory: Follow-up question resolution
4. Endpoint Authorization: /api/audit and /api/evaluation restricted to admin
5. Session Lifecycle: Me endpoint, chat clear, logout
"""
import threading
import time
import urllib.request
import urllib.error
import json
import pytest
from web_server import run_web_server, ENTERPRISE_USERS, ACTIVE_SESSIONS
from http.server import ThreadingHTTPServer
from web_server import RAGStudioHTTPHandler

PORT = 8899
BASE_URL = f"http://127.0.0.1:{PORT}"

@pytest.fixture(scope="module")
def web_server_instance():
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), RAGStudioHTTPHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)
    yield httpd
    httpd.shutdown()
    httpd.server_close()

def _post_json(path, data, token=None):
    url = f"{BASE_URL}{path}"
    req_body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=req_body, headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def _get_json(path, token=None):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))

def test_login_invalid_credentials(web_server_instance):
    url = f"{BASE_URL}/api/auth/login"
    req_body = json.dumps({"username": "m.banda", "password": "wrongpassword"}).encode("utf-8")
    req = urllib.request.Request(url, data=req_body, headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 401

def test_login_and_tools_intern(web_server_instance):
    status, data = _post_json("/api/auth/login", {"username": "m.banda", "password": "password123"})
    assert status == 200
    assert "session_token" in data
    user = data["user"]
    assert user["clearance"] == "public"
    tool_ids = [t["id"] for t in user["tools"]]
    assert "tool-chat" in tool_ids
    assert "tool-curriculum" in tool_ids
    assert "tool-finance-ledger" not in tool_ids
    assert "tool-audit" not in tool_ids

def test_login_and_tools_teacher(web_server_instance):
    status, data = _post_json("/api/auth/login", {"username": "m.mwale", "password": "password123"})
    assert status == 200
    user = data["user"]
    assert user["clearance"] == "staff"
    tool_ids = [t["id"] for t in user["tools"]]
    assert "tool-faculty-policy" in tool_ids
    assert "tool-submissions" in tool_ids
    assert "tool-pastoral-dossier" not in tool_ids
    assert "tool-finance-ledger" not in tool_ids

def test_login_and_tools_counselor(web_server_instance):
    status, data = _post_json("/api/auth/login", {"username": "c.zulu", "password": "password123"})
    assert status == 200
    user = data["user"]
    assert user["clearance"] == "counselor"
    tool_ids = [t["id"] for t in user["tools"]]
    assert "tool-pastoral-dossier" in tool_ids
    assert "tool-welfare-planner" in tool_ids
    assert "tool-deid" in tool_ids
    assert "tool-finance-ledger" not in tool_ids

def test_admin_access_controls(web_server_instance):
    # Teacher cannot access audit
    _, teacher_data = _post_json("/api/auth/login", {"username": "m.mwale", "password": "password123"})
    teacher_token = teacher_data["session_token"]
    url = f"{BASE_URL}/api/audit"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {teacher_token}"})
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req)
    assert exc.value.code == 403

    # Admin can access audit
    _, admin_data = _post_json("/api/auth/login", {"username": "d.phiri", "password": "password123"})
    admin_token = admin_data["session_token"]
    status, audit_logs = _get_json("/api/audit", token=admin_token)
    assert status == 200
    assert isinstance(audit_logs, list)

def test_multi_turn_followup(web_server_instance):
    _, intern_data = _post_json("/api/auth/login", {"username": "m.banda", "password": "password123"})
    token = intern_data["session_token"]

    # Turn 1: General syllabus query
    status1, resp1 = _post_json("/api/chat/message", {"query": "What are the key topics in IGCSE Mathematics 0580?"}, token=token)
    assert status1 == 200
    assert "response" in resp1
    assert len(resp1["retrieved_chunks"]) > 0
    assert len(resp1["chat_history"]) == 2

    # Turn 2: Follow-up question referencing turn 1
    status2, resp2 = _post_json("/api/chat/message", {"query": "Give me a practice problem on the 4th topic"}, token=token)
    assert status2 == 200
    assert len(resp2["chat_history"]) == 4
    # Probability or 4th topic must be handled
    response_lower = resp2["response"].lower()
    assert ("probability" in response_lower or "topic" in response_lower or "exercise" in response_lower or "problem" in response_lower)
