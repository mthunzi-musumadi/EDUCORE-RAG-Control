# ==============================================================================
# EDUCORE SERVICES - ENTERPRISE AI RAG & OPEN WEBUI LAUNCHER (POWERSHELL)
# Strict ISO/IEC 42001:2023 & Zambian Data Protection Act No. 3 Governance
# ==============================================================================
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  STARTING EDUCORE SERVICES ENTERPRISE RAG PLATFORM" -ForegroundColor White
Write-Host "  Dual-Track Governance: Enterprise Operations & Academic Transformation" -ForegroundColor Gray
Write-Host "  Frontend: Open WebUI | Backend: ISO 42001 Governed OpenAI API" -ForegroundColor Gray
Write-Host "==============================================================================" -ForegroundColor Cyan

# 0. Pre-Flight Cleanup: Clear legacy remote DB variables & release ports 8000 / 3000
Write-Host "[PRE-FLIGHT] Resetting environment and releasing ports..." -ForegroundColor Cyan
Remove-Item env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item env:WEBUI_SECRET_KEY -ErrorAction SilentlyContinue

$LingeringConns = Get-NetTCPConnection -LocalPort 8000, 3000 -ErrorAction SilentlyContinue
if ($LingeringConns) {
    Write-Host "  Stopping previous instances on ports 8000 / 3000..." -ForegroundColor Yellow
    $LingeringConns | ForEach-Object {
        if ($_.OwningProcess -gt 0) {
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 1
}

# 1. Open WebUI & Ollama Environment Configurations (Optimized for Intel Core i3-10100T 4C/8T 35W)
$env:OPENAI_API_BASE_URL = "http://127.0.0.1:8000/v1"
$env:OPENAI_API_KEY = "educore-enterprise-key"
$env:ENABLE_OLLAMA_API = "False"              # Expose only Educore governed models; hide raw llama3.2 & nomic-embed-text
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:OLLAMA_NUM_PARALLEL = "1"              # Dedicate all cores to single-stream inference without context thrashing
$env:OLLAMA_MAX_LOADED_MODELS = "2"         # Keep qwen2.5:1.5b and nomic-embed-text warm in memory
$env:OLLAMA_KEEP_ALIVE = "-1"               # Prevent model swapping and unload (pinned indefinitely)
$env:OLLAMA_FLASH_ATTENTION = "1"           # Accelerates attention computation and cuts KV-cache bandwidth
$env:OLLAMA_KV_CACHE_TYPE = "q8_0"          # Quantizes KV cache to 8-bit to fit closer to L3 cache
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
$env:DATA_DIR = "$RootDir\data\openwebui"

# 2. Launch Backend
Write-Host "[1/2] Launching Educore Enterprise RAG Governance Server (Port 8000)..." -ForegroundColor Yellow
$BackendPython = Join-Path $RootDir "framework_control\Scripts\python.exe"
$BackendScript = Join-Path $RootDir "src\backend\educore_enterprise_backend.py"
Start-Process -FilePath $BackendPython -ArgumentList "`"$BackendScript`" 8000" -WindowStyle Normal

Start-Sleep -Seconds 3

# 3. Launch Decoupled Educore Enterprise Frontend (Route B)
Write-Host "[2/2] Launching Educore Enterprise Frontend (Port 3000)..." -ForegroundColor Green
$FrontendScript = Join-Path $RootDir "serve_frontend.py"
Start-Process -FilePath $BackendPython -ArgumentList "`"$FrontendScript`" 3000" -WindowStyle Normal

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  Educore Enterprise Platform Online (Route B Decoupled Architecture)!" -ForegroundColor Green
Write-Host "  - Frontend UI:  http://localhost:3000" -ForegroundColor White
Write-Host "  - Backend API:  http://127.0.0.1:8000/v1" -ForegroundColor White
Write-Host "  - Audit Ledger: http://127.0.0.1:8000/api/audit" -ForegroundColor White
Write-Host "  - Audit File:   $RootDir\aims_rag_audit.jsonl" -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor Cyan
