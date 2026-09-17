# ==============================================================================
# EDUCORE SERVICES - ENTERPRISE AI RAG & OPEN WEBUI LAUNCHER (POWERSHELL)
# Strict ISO/IEC 42001:2023 & Zambian Data Protection Act No. 3 Governance
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  STARTING EDUCORE SERVICES ENTERPRISE RAG PLATFORM" -ForegroundColor White
Write-Host "  Dual-Track Governance: Enterprise Operations & Academic Transformation" -ForegroundColor Gray
Write-Host "  Frontend: Open WebUI | Backend: ISO 42001 Governed OpenAI API" -ForegroundColor Gray
Write-Host "==============================================================================" -ForegroundColor Cyan

# 1. Open WebUI & Ollama Environment Configurations (Optimized for Intel Core i3-10100T 4C/8T 35W)
$env:OPENAI_API_BASE_URL = "http://127.0.0.1:8000/v1"
$env:OPENAI_API_KEY = "educore-enterprise-key"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:OLLAMA_NUM_PARALLEL = "1"              # Dedicate all 4 cores to single-stream inference without context thrashing
$env:OLLAMA_MAX_LOADED_MODELS = "2"         # Keep llama3.2:1b and nomic-embed-text warm in memory
$env:OLLAMA_KEEP_ALIVE = "30m"              # Prevent cold-start disk overhead on desktop drive
$env:PORT = "3000"
$env:WEBUI_PORT = "3000"
$env:WEBUI_NAME = "Educore Services Enterprise AI"
$env:DEFAULT_MODELS = "educore-enterprise-all"
$env:ENABLE_SIGNUP = "True"
$env:WEBUI_AUTH = "True"
$env:ENABLE_FORWARD_USER_INFO_HEADERS = "True"
$env:RAG_EMBEDDING_ENGINE = "ollama"
$env:RAG_EMBEDDING_MODEL = "nomic-embed-text"
$env:RAG_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:HF_HUB_OFFLINE = "1"
$env:TRANSFORMERS_OFFLINE = "1"

# 2. Launch Backend
Write-Host "[1/2] Launching Educore Enterprise RAG Governance Server (Port 8000)..." -ForegroundColor Yellow
$BackendPython = Join-Path $ScriptDir "framework_control\Scripts\python.exe"
$BackendScript = Join-Path $ScriptDir "educore_enterprise_backend.py"
Start-Process -FilePath $BackendPython -ArgumentList "`"$BackendScript`" 8000" -WindowStyle Normal

Start-Sleep -Seconds 3

# 3. Launch Open WebUI
Write-Host "[2/2] Launching Open WebUI Frontend (Port 3000)..." -ForegroundColor Green
$WebUIExe = Join-Path $ScriptDir ".openwebui_env\Scripts\open-webui.exe"
Start-Process -FilePath $WebUIExe -ArgumentList "serve --port 3000" -WindowStyle Normal

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  EduCore Enterprise Platform Online!" -ForegroundColor Green
Write-Host "  - Backend API: http://127.0.0.1:8000/v1" -ForegroundColor White
Write-Host "  - Open WebUI:  http://127.0.0.1:3000" -ForegroundColor White
Write-Host "  - Audit Log:   $ScriptDir\aims_rag_audit.jsonl" -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor Cyan
