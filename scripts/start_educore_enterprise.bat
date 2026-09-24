@echo off
REM ==============================================================================
REM EDUCORE SERVICES - ENTERPRISE AI RAG & OPEN WEBUI LAUNCHER
REM Strict ISO/IEC 42001:2023 & Zambian Data Protection Act No. 3 Governance
REM ==============================================================================
echo ==============================================================================
echo   STARTING EDUCORE SERVICES ENTERPRISE RAG PLATFORM
echo   Dual-Track Governance: Enterprise Operations ^& Academic Transformation
echo   Frontend: Open WebUI ^| Backend: ISO 42001 Governed OpenAI API
echo ==============================================================================

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%.."
set ROOT_DIR=%cd%

REM 1. Set Open WebUI & Ollama Configurations (Optimized for Intel Core i3-10100T 4C/8T 35W)
set OPENAI_API_BASE_URL=http://127.0.0.1:8000/v1
set OPENAI_API_KEY=educore-enterprise-key
set ENABLE_OLLAMA_API=False
set OLLAMA_BASE_URL=http://127.0.0.1:11434
set OLLAMA_NUM_PARALLEL=1
set OLLAMA_MAX_LOADED_MODELS=2
set OLLAMA_KEEP_ALIVE=-1
set OLLAMA_FLASH_ATTENTION=1
set OLLAMA_KV_CACHE_TYPE=q8_0
set PORT=3000
set WEBUI_PORT=3000
set WEBUI_NAME=Educore Services Enterprise AI
set DEFAULT_MODELS=educore-enterprise-all
set ENABLE_SIGNUP=True
set WEBUI_AUTH=True
set ENABLE_FORWARD_USER_INFO_HEADERS=True
set RAG_EMBEDDING_ENGINE=ollama
set RAG_EMBEDDING_MODEL=nomic-embed-text
set RAG_OLLAMA_BASE_URL=http://127.0.0.1:11434
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
set DATA_DIR=%ROOT_DIR%\data\openwebui

REM 2. Start Educore Governance RAG Server in Background
echo [1/2] Launching Educore Enterprise RAG Governance Server (Port 8000)...
start "Educore Governance Server" "%ROOT_DIR%\framework_control\Scripts\python.exe" "%ROOT_DIR%\src\backend\educore_enterprise_backend.py" 8000

REM Wait 3 seconds for backend to bind port
timeout /t 3 /nobreak >nul

REM 3. Start Decoupled Educore Enterprise Frontend (Route B)
echo [2/2] Launching Educore Enterprise Frontend (Port 3000)...
start "Educore Enterprise Frontend" "%ROOT_DIR%\framework_control\Scripts\python.exe" "%ROOT_DIR%\serve_frontend.py" 3000

echo ==============================================================================
echo   EduCore Enterprise Platform Online (Route B Decoupled Architecture)!
echo   - Frontend UI:  http://localhost:3000
echo   - Backend API:  http://127.0.0.1:8000/v1
echo   - Audit Ledger: http://127.0.0.1:8000/api/audit
echo   - Audit File:   %ROOT_DIR%\aims_rag_audit.jsonl
echo ==============================================================================
pause
