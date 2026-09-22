import os
import sys
import subprocess
import hashlib
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Auto-re-execute using project virtual environment if dependencies are missing
_VENV_PYTHON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "framework_control", "Scripts", "python.exe"))
if os.path.exists(_VENV_PYTHON) and os.path.normpath(sys.executable).lower() != os.path.normpath(_VENV_PYTHON).lower():
    try:
        import docling  # noqa: F401
    except ImportError:
        res = subprocess.run([_VENV_PYTHON] + sys.argv, env=os.environ)
        sys.exit(res.returncode)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

from docling.document_converter import DocumentConverter
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from langchain_core.documents import Document

# Allow importing document_readers from the backend package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from document_readers import read_document

# ==============================================================================
# 1. LOCALIZED PII RECOGNIZERS (ZAMBIA)
# ==============================================================================
def get_zambian_nrc_recognizer() -> PatternRecognizer:
    """
    Recognizes Zambian National Registration Card (NRC) numbers.
    Standard format: 6 digits / 2 digits / 1 digit (e.g., 123456/11/1).
    """
    nrc_pattern = Pattern(
        name="zambian_nrc_pattern",
        regex=r"\b\d{6}/\d{2}/\d{1}\b",
        score=0.95
    )
    return PatternRecognizer(
        supported_entity="ZAMBIAN_NRC",
        patterns=[nrc_pattern],
        context=["nrc", "identity", "registration", "national registration", "card"]
    )

def get_zambian_phone_recognizer() -> PatternRecognizer:
    """
    Recognizes Zambian domestic phone numbers across all networks
    (097/077 Airtel, 096/076 MTN, 095/075 Zamtel) with or without country code (+260).
    """
    zambia_phone_pattern = Pattern(
        name="zambian_phone_pattern",
        regex=r"(?:\+?260|0)[-.\s]*(?:9[5-7]|7[5-79])(?:[-.\s]*\d){7}\b",
        score=0.95
    )
    return PatternRecognizer(
        supported_entity="PHONE_NUMBER",
        patterns=[zambia_phone_pattern],
        context=["phone", "call", "mobile", "tel", "contact", "whatsapp", "cell"]
    )

# ==============================================================================
# 2. CORE INGESTION & DE-IDENTIFICATION PIPELINE
# ==============================================================================
class IngestionDeidentificationPipeline:
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        # 1. Document Converter is lazy-loaded to prevent unwanted network egress
        self._doc_converter = None

        # 2. Setup Presidio Analyzer with Default + Custom Recognizers
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()

        # Register Zambian localized pattern recognizers
        registry.add_recognizer(get_zambian_nrc_recognizer())
        registry.add_recognizer(get_zambian_phone_recognizer())

        self.analyzer = AnalyzerEngine(
            registry=registry,
            supported_languages=["en"]
        )

        # 3. Setup Presidio Anonymizer
        self.anonymizer = AnonymizerEngine()

        # Target entities to redact before vector storage
        self.target_entities = [
            "PERSON",
            "PHONE_NUMBER",
            "EMAIL_ADDRESS",
            "LOCATION",
            "ZAMBIAN_NRC",
            "IBAN_CODE",
            "CREDIT_CARD"
        ]

    @property
    def doc_converter(self):
        """Lazy-initializes Docling converter only if explicitly requested."""
        if self._doc_converter is None:
            from docling.document_converter import DocumentConverter
            self._doc_converter = DocumentConverter()
        return self._doc_converter

    def _compute_sha256(self, file_path: str) -> str:
        """Calculates cryptographic hash of source files for audit provenance."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def extract_text(self, file_path: str, page_range: Optional[Tuple[int, int]] = None) -> str:
        """
        Extracts text from a document file, dispatching by format.
        Uses 100% offline, zero-egress document_readers (pypdfium2, python-docx, openpyxl).

        Returns the extracted text as a single string.
        """
        clean_title, sections = read_document(file_path, page_range=page_range)
        return "\n\n".join(
            section["content"] for section in sections if section.get("content")
        )

    def extract_text_from_pdf(self, file_path: str, page_range: Tuple[int, int] = (1, 2)) -> str:
        """
        Backward-compatible wrapper around extract_text.
        Parses PDF layout and runs OCR when necessary via Docling.
        Exports reading-order Markdown. Restricts page range for performant batching.
        """
        return self.extract_text(file_path, page_range=page_range)

    def deidentify_text(self, text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Runs Presidio detection and replaces PII with labeled tokens.
        Tracks entity transformations for data quality and provenance.
        """
        findings = self.analyzer.analyze(
            text=text,
            entities=self.target_entities,
            language="en"
        )

        operators = {
            entity: OperatorConfig("replace", {"new_value": f"[REDACTED_{entity}]"})
            for entity in self.target_entities
        }

        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=findings,
            operators=operators
        )

        redaction_log = [
            {
                "entity_type": finding.entity_type,
                "start": finding.start,
                "end": finding.end,
                "confidence": round(finding.score, 2)
            }
            for finding in findings
        ]

        return anonymized_result.text, redaction_log

    def process_document(
        self,
        file_path: str,
        campus: str,
        clearance: str,
        category: str,
        doc_id: str,
        page_range: Optional[Tuple[int, int]] = None
    ) -> Document:
        """
        Full multi-format pipeline: File ingestion -> Text extraction -> Presidio De-ID -> LangChain Document.

        Supports PDF (via Docling OCR), DOCX, XLSX, CSV, TXT and other formats
        handled by the document_readers module.
        Attaches immutable provenance and quality metadata (ISO 42001 A.7.5 & A.7.6).
        """
        file_hash = self._compute_sha256(file_path)
        file_name = Path(file_path).name
        ext = Path(file_path).suffix.lower()

        # 1. OCR / Text extraction (format-aware)
        raw_text = self.extract_text(file_path, page_range=page_range)

        # 2. De-identification
        clean_text, redaction_log = self.deidentify_text(raw_text)

        # Determine pages_processed label based on file format
        if ext == ".pdf" and page_range is not None:
            pages_processed = f"{page_range[0]}-{page_range[1]}"
        elif ext in (".xlsx", ".xls"):
            pages_processed = "all_sheets"
        elif ext == ".docx":
            pages_processed = "all_sections"
        else:
            pages_processed = "full_document"

        # 3. ISO 42001 Provenance & Data Preparation Metadata
        metadata = {
            "doc_id": doc_id,
            "source_file": file_name,
            "source_sha256": file_hash,
            "campus": campus,
            "clearance": clearance,
            "category": category,
            "ingestion_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "pages_processed": pages_processed,
            "pii_entities_redacted": len(redaction_log),
            "redaction_summary": {
                entity: sum(1 for r in redaction_log if r["entity_type"] == entity)
                for entity in set(r["entity_type"] for r in redaction_log)
            }
        }

        # 4. Write provenance trace to audit ledger
        self._record_provenance_log(metadata)

        return Document(page_content=clean_text, metadata=metadata)

    def _record_provenance_log(self, metadata: Dict[str, Any]):
        """Persists document ingestion history to an append-only ledger."""
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        log_path = os.path.join(root, "data", "logs", "data_provenance_audit.jsonl")
        if not os.path.exists(os.path.dirname(log_path)):
            log_path = "data_provenance_audit.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(metadata) + "\n")

# ==============================================================================
# 3. VERIFICATION AND TESTING RUNNER (MODULE LEVEL)
# ==============================================================================
def run_pipeline_demo(test_pdf_file: str = None):
    """Runs the full visual demonstration of text and PDF de-identification."""
    if test_pdf_file is None:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        fixture_pdf = os.path.join(root, "tests", "fixtures", "sample_document.pdf")
        test_pdf_file = fixture_pdf if os.path.exists(fixture_pdf) else "c06640111.pdf"
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        console = Console()

        header = (
            "[bold cyan]PRESIDIO & DOCLING MULTIMODAL PII DE-IDENTIFICATION PIPELINE[/bold cyan]\n"
            "[bold white]Compliance: ISO 42001 Clause 7.5 & A.7.6 / GDPR / Zambian National Identity[/bold white]\n"
            "[dim]Presidio Redaction Engine | RapidOCR ONNX Layout Parser | Append-Only Provenance Ledger[/dim]"
        )
        console.print(Panel(header, border_style="cyan", box=box.DOUBLE))
    except Exception:
        print("=" * 70, flush=True)
        print(">>> Initializing Ingestion & De-Identification Pipeline...", flush=True)
        print("=" * 70, flush=True)

    pipeline = IngestionDeidentificationPipeline()

    sample_raw_text = """
    SENTINEL KABITAKA CONFIDENTIAL PASTORAL ASSESSMENT
    Date: 12 August 2026
    Student Name: Mwape Tembo
    NRC Number: 489211/10/1
    Guardian: Alice Chanda
    Contact Mobile: +260 97 1234567
    Alternate Contact: 0966889900
    Residential Location: Plot 42 Kabulonga Road, Lusaka
    Email: achanda@example.co.zm

    Pastoral Notes:
    The student has expressed difficulty adjusting to the Cambridge Extended Math (0580)
    workload due to family bereavement. Monitoring recommended across Term 2.
    """

    clean_text, redactions = pipeline.deidentify_text(sample_raw_text)

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table
        from rich import box
        console = Console()

        # Text Sanitization Panels
        console.print("\n[bold]1. Unstructured Text De-Identification Demonstration[/bold]")
        console.print(Panel(sample_raw_text.strip(), title="Raw Input with PII (Zambian NRC, Phone, Email, Person)", border_style="red", box=box.ROUNDED))
        console.print(Panel(clean_text.strip(), title="Sanitized Context Output ([REDACTED_*] Tokens)", border_style="green", box=box.ROUNDED))

        # Redacted Entities Table
        table = Table(title="Detected PII Entities & Confidence Provenance Ledger", box=box.ROUNDED)
        table.add_column("Entity Type", style="bold cyan")
        table.add_column("Confidence Score", justify="right", style="green")
        table.add_column("Char Range", style="dim")
        table.add_column("Protection Policy", style="yellow")

        for r in redactions:
            etype = r["entity_type"]
            policy = "Child Safeguarding / GDPR" if etype in ["PERSON", "ZAMBIAN_NRC", "PHONE_NUMBER"] else "Location Privacy"
            table.add_row(etype, f"{r['confidence'] * 100:.0f}%", f"{r['start']}-{r['end']}", policy)

        console.print(table)

        # PDF Ingestion Demo
        console.print("\n[bold]2. Multimodal PDF Ingestion & OCR Layout Extraction[/bold]")
        if os.path.exists(test_pdf_file):
            with console.status(f"[bold green]Parsing layout and redacting PII from {test_pdf_file} (Pages 1-2 via Docling)...[/bold green]"):
                doc = pipeline.process_document(
                    file_path=test_pdf_file,
                    campus="sentinel",
                    clearance="staff",
                    category="curriculum",
                    doc_id="DOC-001",
                    page_range=(1, 2)
                )

            prov = doc.metadata
            prov_table = Table(title="Document Ingestion Provenance Record (data_provenance_audit.jsonl)", box=box.ROUNDED)
            prov_table.add_column("Metadata Field", style="bold white")
            prov_table.add_column("Recorded Provenance Value", style="cyan")

            prov_table.add_row("Document ID", prov.get("doc_id"))
            prov_table.add_row("Source File", prov.get("source_file"))
            prov_table.add_row("Cryptographic SHA-256", prov.get("source_sha256")[:32] + "...")
            prov_table.add_row("Campus Boundary", prov.get("campus").upper())
            prov_table.add_row("Operational Clearance", prov.get("clearance").upper())
            prov_table.add_row("Pages Processed", prov.get("pages_processed"))
            prov_table.add_row("Total Redacted Entities", str(prov.get("pii_entities_redacted")))
            prov_table.add_row("Ingestion UTC Timestamp", prov.get("ingestion_timestamp"))

            console.print(prov_table)
            console.print(Panel(doc.page_content[:400].strip() + "\n...", title=f"Sanitized Markdown Preview ({len(doc.page_content)} characters)", border_style="blue", box=box.ROUNDED))
        else:
            console.print(f"[yellow]Notice: Sample file '{test_pdf_file}' not found. Skipped PDF extraction.[/yellow]")

        console.print(Panel(
            "[bold green]PII DE-IDENTIFICATION & PROVENANCE PIPELINE READY[/bold green]\n"
            "[dim]To test interactively in the web dashboard, run:[/dim] [bold cyan]python pdf_deid_pipeline.py --web[/bold cyan]",
            border_style="green",
            box=box.ROUNDED
        ))
    except Exception:
        print("\n[SANITIZED TEXT OUTPUT]:\n", clean_text)
        print("\n[REDACTED ENTITIES LOGGED]:")
        for r in redactions:
            print(f"  - Entity: {r['entity_type']} (Confidence: {r['confidence']})")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Presidio & Docling Multimodal De-Identification Pipeline")
    parser.add_argument("--web", "-w", action="store_true", help="Launch interactive browser-based web dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind web dashboard (default 8080)")
    parser.add_argument("--pdf", type=str, default="c06640111.pdf", help="Target PDF file to ingest")
    args = parser.parse_args()

    if args.web:
        from web_server import run_web_server
        run_web_server(port=args.port, open_browser=True)
    else:
        run_pipeline_demo(test_pdf_file=args.pdf)