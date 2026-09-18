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
.
├── app.py                              # Core retrieval + LLM demo pipeline
├── educore_enterprise_backend.py       # Enterprise backend logic
├── student_socratic_rag.py             # Student-focused RAG flow
├── build_framework_corpus.py           # Corpus-building utility
├── data.txt                            # Source dataset for demo retrieval
├── requirements.txt                    # Python dependencies
├── requirements_openwebui.txt          # Open WebUI-related dependencies
├── OPEN_WEBUI_SETUP.md                 # Setup and operations guide
├── Modelfile.i3-10100t                # Local model run config
├── aims_rag_audit.jsonl               # Audit ledger example
├── framework_summary.json              # Framework summary metadata
├── guardrail_stress_test.txt           # Guardrail testing notes
├── setup_openwebui_rbac.py            # RBAC provisioning setup script
├── start_educore_enterprise.ps1        # Windows launch script
├── start_educore_enterprise.bat        # Windows batch launcher
├── EDUCORE_AI_FRAMEWORK/               # Governance/documentation corpus
├── production_setup/                   # Production-related design, eval, and server files
├── chroma_enterprise_store/            # Chroma persistence directory
├── test_*.py                           # Various safeguard and integration tests
└── README.md                          # Project overview and usage guide
```

## Tech stack

- Python
- LangChain
- ChromaDB
- Ollama
- FastAPI / web server components
- Open WebUI integration
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

Typical model examples:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 4. Run the core demo pipeline

```bash
python app.py
```

This starts the local RAG/email-generation workflow using the included dataset and embedded model stack.

## Running the enterprise setup

For the full institutional deployment workflow, follow the setup and operational guidance in `OPEN_WEBUI_SETUP.md`.

On Windows, you can launch the packaged enterprise flow with:

```powershell
./start_educore_enterprise.ps1
```

or

```cmd
start_educore_enterprise.bat
```

## Production and governance assets

The repository also includes a production-focused subfolder under `production_setup/` with:
- `DESIGN.md` for UI and experience design
- `PRODUCT.md` for product context and persona model
- evaluation and testing scripts
- web server and RAG pipeline examples
- sample audit and evaluation datasets

These files provide a more complete picture of how the RAG system is meant to be used in a governed enterprise environment.

## Testing

The repository includes automated test coverage for backend, security, and integration scenarios. Common commands include:

```bash
pytest
```

You can also run targeted checks such as:

```bash
pytest test_educore_enterprise_backend.py
pytest test_rag_security.py
pytest test_http_endpoints.py
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
