import urllib.request
import subprocess
import time
import sys
import os

python_exe = os.path.abspath(r"framework_control\Scripts\python.exe")
frontend_server = subprocess.Popen([python_exe, "serve_frontend.py", "3007"])
time.sleep(2)

try:
    # 1. Fetch index.html
    req = urllib.request.urlopen("http://127.0.0.1:3007/")
    html = req.read().decode('utf-8')
    assert req.status == 200, f"Expected 200, got {req.status}"
    assert "Educore Enterprise RAG" in html, "Page title missing"
    print("[OK] index.html successfully served")

    # 2. Extract css url and verify contents
    import re
    css_match = re.search(r'href="(/assets/index-[^"]+\.css)"', html)
    if css_match:
        css_url = f"http://127.0.0.1:3007{css_match.group(1)}"
        req_css = urllib.request.urlopen(css_url)
        css_text = req_css.read().decode('utf-8')
        assert "--background" in css_text, "CSS variables missing from compiled bundle"
        print(f"[OK] CSS bundle successfully served ({len(css_text)} bytes) with verified CSS variables")

    # 3. Verify images
    req_logo = urllib.request.urlopen("http://127.0.0.1:3007/educore.png")
    assert req_logo.status == 200, "educore.png missing"
    print("[OK] educore.png successfully served")

    req_logo_e = urllib.request.urlopen("http://127.0.0.1:3007/educore-rag-e.png")
    assert req_logo_e.status == 200, "educore-rag-e.png missing"
    print("[OK] educore-rag-e.png successfully served")

    print("\nALL FRONTEND ASSET TESTS PASSED!")
finally:
    frontend_server.terminate()
    frontend_server.wait()
