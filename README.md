# EDUCORE RAG Control

EDUCORE RAG Control is a Python-based enterprise retrieval-augmented generation (RAG) and governance project focused on controlled institutional AI use, role-based access control, document retrieval, and safe knowledge-grounded chat experiences.

This repository combines:
- a local RAG pipeline built with LangChain, Chroma, and Ollama
- enterprise governance and filtering logic
- document ingestion and auditing flows
- Open WebUI integration guidance for institutional deployment
- production-oriented evaluation and backend components

## Project purpose

The project is designed to support AI-assisted operations in an educational and institutional environment with clear guardrails, clearance boundaries, and auditability. It includes components for:
- secure retrieval from curated knowledge sources
- role-based access restrictions and policy enforcement
- safety-oriented filtering for sensitive information
- generation grounded in internal documentation
- deployment patterns for enterprise-style web UIs

## Core capabilities

- Retrieval-augmented generation over local corpora and structured files
- Metadata-aware document retrieval and filtering
- PII sanitization and controlled data handling
- Governance-enforced chat/backend workflows
- Open WebUI setup and RBAC administration guidance
- Evaluation and testing for RAG behavior and security enforcement

## Repository structure

```text
EDUCORE-RAG-Control/
├── src/                                # Modular Application Code
│   ├── backend/                        # Enterprise API & sync engine
│   │   ├── educore_enterprise_backend.py  # Governed OpenAI API backend (Port 8000)
│   │   ├── framework_sync_service.py   # Real-time SHA-256 document watcher & Chroma upsert
│   │   └── tps_counter.py              # Performance telemetry & TPS tracker
│   ├── governance/                     # Open WebUI security & RBAC integration
│   │   ├── educore_framework_filter.py # Open WebUI governance filter & clearance valves
│   │   ├── setup_openwebui_rbac.py     # Open WebUI DB user/group/model ACL provisioning
│   │   └── apply_educore_logos.py      # Institutional branding & logo provisioning
│   ├── ingestion/                      # Document ingestion & de-identification
│   │   └── pdf_deid_pipeline.py        # Presidio + Docling multimodal PII redaction
│   └── evaluation/                     # ISO 42001 & NIST AI RMF evaluation engine
│       └── rag_evaluator.py            # Faithfulness, relevance, context precision/recall
│
├── data/                               # Data Stores & Working Corpora
│   ├── corpus/                         # Active structured JSON corpora & sync state
│   │   ├── enterprise_data.json
│   │   └── corpus_sync_state.json
│   ├── eval/                           # NIST AI RMF benchmark datasets & results
│   │   ├── evaluation_dataset.json
│   │   └── rag_eval_results.json
│   └── logs/                           # ISO 42001 compliance audit trails
│       ├── aims_rag_audit.jsonl
│       └── data_provenance_audit.jsonl
│
├── assets/                             # Institutional visual assets
│   ├── educore.png                     # Primary logo
│   └── educore-rag-e.png               # RAG platform emblem
│
├── docs/                               # Documentation & hardware configs
│   ├── OPEN_WEBUI_SETUP.md             # Complete Open WebUI deployment guide
│   └── Modelfile.i3-10100t             # Hardware-optimized Ollama Modelfile
│
├── studio/                             # Standalone RAG Studio Prototype
│   ├── web_server.py                   # Standalone HTTP server & API
│   ├── production_rag.py               # Prototype access-controlled retriever
│   ├── dashboard.html                  # Standalone single-page web UI
│   └── PRODUCT.md                      # Product context & persona boundaries
│
├── EDUCORE_AI_FRAMEWORK/               # Governed Institutional Policy Documents (.docx)
│   ├── educore-doc-00-master-launch-directory-v3-0.docx
│   ├── 00_HUB_MASTER/
│   │   └── educore-ai-framework-implementation-handbook-v2-0.docx
│   ├── 01_SPOKES_POLICIES/
│   │   ├── educore-doc-01-organizational-governance-policy-v3-0.docx
│   │   └── educore-doc-02-implementation-action-plan-v3-0.docx
│   ├── 02_SPOKES_AUDIT/
│   │   └── educore-doc-03-pre-rollout-discovery-survey-v3-0.docx
│   └── 03_SPOKES_AUDIT_TECH/
│       └── educore-cognitive-bypass-audit-checklist-v2-0.docx
│
├── tests/                              # Unified Automated Test Suite
│   ├── conftest.py                     # Environment & sys.path configuration
│   ├── unit/                           # Telemetry & multi-turn memory unit tests
│   │   ├── test_tps_telemetry.py
│   │   └── test_multiturn_conciseness.py
│   ├── integration/                    # Backend API, sync, and RBAC tests
│   │   ├── test_educore_enterprise_backend.py
│   │   ├── test_http_endpoints.py
│   │   ├── test_framework_live_sync.py
│   │   └── test_openwebui_rbac_integration.py
│   ├── evaluation/                     # RAG pipeline & studio server tests
│   │   ├── test_rag_pipeline.py
│   │   ├── test_rag_evaluation.py
│   │   └── test_web_server.py
│   └── fixtures/                       # Test documents
│       └── sample_document.pdf
│
├── scripts/                            # Operational & Launch Scripts
│   ├── start_educore_enterprise.ps1    # 1-Click PowerShell launcher
│   └── start_educore_enterprise.bat    # 1-Click Windows batch launcher
│
├── chroma_enterprise_store/            # Chroma persistence directory
├── requirements.txt                    # Python dependencies
└── README.md                           # Project overview and usage guide
```

## Tech stack

- Python 3.10+
- LangChain
- ChromaDB
- Ollama
- Open WebUI
- Microsoft Presidio & Docling
- pytest-based evaluation

## Quick start

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start Ollama and ensure required models are available

This project uses local model inference through Ollama. Before running the app, ensure Ollama is installed and running locally.

```bash
ollama pull qwen2.5:1.5b
ollama pull nomic-embed-text
```

### 4. Running the enterprise setup

For the full institutional deployment workflow, follow the setup and operational guidance in `docs/OPEN_WEBUI_SETUP.md`.

On Windows, you can launch the packaged enterprise flow with:

```powershell
.\scripts\start_educore_enterprise.ps1
```

or

```cmd
scripts\start_educore_enterprise.bat
```

### 5. Running the backend directly

```bash
python src/backend/educore_enterprise_backend.py 8000
```

## Real-Time Document Synchronization & Vector Upsert

The enterprise backend automatically detects changes to framework documents (`.docx`, `.pdf`, `.xlsx`, `.xls`) in `EDUCORE_AI_FRAMEWORK/`, generates embeddings incrementally, and applies zero-downtime atomic upserts to ChromaDB.

### Watch Directories Configuration
By default, the backend monitors `EDUCORE_AI_FRAMEWORK/` recursively. You can configure custom or external watch directories (e.g. OneDrive / SharePoint sync folders, network drives) using:

1. **CLI Flag (`--watch-dir` or `-w`)**:
   ```bash
   python src/backend/educore_enterprise_backend.py --watch-dir "C:\Users\admin\SharePoint\Framework Docs"
   ```

2. **Environment Variable (`EDUCORE_FRAMEWORK_DIR`)**:
   ```bash
   export EDUCORE_FRAMEWORK_DIR="/path/to/framework/docs"
   ```

3. **On-Demand HTTP Sync Trigger**:
   ```bash
   curl -X POST http://localhost:8000/api/framework/sync -H "Content-Type: application/json" -d "{}"
   ```

4. **Sync Status Inspection**:
   ```bash
   curl http://localhost:8000/api/framework/status
   ```

## Testing

The repository includes automated test coverage organized into unit, integration, and evaluation suites:

```bash
# Run all tests
pytest

# Run targeted test suites
pytest tests/unit
pytest tests/integration
pytest tests/evaluation
```

## Notes

This project is best understood as an experimental but operationally structured enterprise RAG solution. It blends technical AI tooling with compliance-oriented institutional requirements, access control boundaries, and audit logging.

## License

No explicit license file is present in this repository at the moment. If you plan to distribute or reuse this project, confirm the licensing status before publishing or commercial use.

## Contributing

Contributions are welcome if they improve:
- governance and safety behaviors
- retrieval quality
- security testing coverage
- deployment clarity
- documentation quality

## Contact

For project-specific questions or collaboration, use the repository owner and issue tracker associated with this GitHub project.
