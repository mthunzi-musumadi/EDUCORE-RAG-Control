# ==============================================================================
# EDUCORE ENTERPRISE - FRAMEWORK DOCUMENT SYNCHRONIZATION SERVICE
# Real-time SHA-256 Change Detection, Dynamic Extraction & Incremental Chunking
# Compliance: ISO/IEC 42001:2023 | Zambian Data Protection Act No. 3 of 2021
# ==============================================================================
import os
import re
import json
import hashlib
import time
from typing import Dict, Any, List, Tuple, Optional, Union
import docx
from document_readers import read_document, SUPPORTED_EXTENSIONS, get_format_prefix
from tps_counter import TELEMETRY

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def _resolve_project_root() -> str:
    env_root = os.environ.get("BASE_DIR") or os.environ.get("EDUCORE_BASE_DIR")
    if env_root and os.path.exists(env_root):
        return os.path.abspath(env_root)
    curr = CURRENT_DIR
    for _ in range(4):
        if os.path.exists(os.path.join(curr, "EDUCORE_AI_FRAMEWORK")) or os.path.exists(os.path.join(curr, "data")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    return os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

BASE_DIR = _resolve_project_root()
FRAMEWORK_DIR = os.environ.get(
    "EDUCORE_FRAMEWORK_DIR",
    os.path.join(BASE_DIR, "EDUCORE_AI_FRAMEWORK")
)

_candidate_data_paths = [
    os.path.join(BASE_DIR, "data", "corpus", "enterprise_data.json"),
    os.path.join(BASE_DIR, "production_setup", "enterprise_data.json")
]
DATA_PATH = next((p for p in _candidate_data_paths if os.path.exists(p)), _candidate_data_paths[0])

_candidate_state_paths = [
    os.path.join(BASE_DIR, "data", "corpus", "corpus_sync_state.json"),
    os.path.join(BASE_DIR, "production_setup", "corpus_sync_state.json")
]
STATE_PATH = next((p for p in _candidate_state_paths if os.path.exists(p)), _candidate_state_paths[0])

def resolve_watch_dirs(custom_dirs: Optional[Union[str, List[str]]] = None) -> List[str]:
    """
    Resolves watch directories from parameter, EDUCORE_FRAMEWORK_DIR env var,
    or the default project EDUCORE_AI_FRAMEWORK directory.
    Supports semicolon (;) or comma (,) separated paths in env vars or strings.
    """
    if custom_dirs:
        if isinstance(custom_dirs, str):
            raw_list = [p.strip() for p in re.split(r'[;,]', custom_dirs) if p.strip()]
        else:
            raw_list = [str(p).strip() for p in custom_dirs if str(p).strip()]
    else:
        env_val = os.environ.get("EDUCORE_FRAMEWORK_DIR", "").strip()
        if env_val:
            raw_list = [p.strip() for p in re.split(r'[;,]', env_val) if p.strip()]
        else:
            raw_list = [os.path.join(BASE_DIR, "EDUCORE_AI_FRAMEWORK")]

    resolved = []
    for p in raw_list:
        abs_p = os.path.abspath(os.path.expanduser(p))
        if abs_p not in resolved:
            resolved.append(abs_p)
    return resolved

# Default metadata mappings based on framework folder structure
FOLDER_METADATA_MAP = {
    "00_HUB_MASTER": {
        "clearance": "staff",
        "category": "governance",
        "classification": "INTERNAL - AIMS HANDBOOK",
        "purview_label": "Internal - Educational",
        "allowed_roles": ["staff", "counselor", "admin"],
        "campus": "all"
    },
    "01_SPOKES_POLICIES": {
        "clearance": "staff",
        "category": "policy",
        "classification": "INTERNAL - GOVERNANCE POLICY",
        "purview_label": "Internal - Educational",
        "allowed_roles": ["staff", "counselor", "admin"],
        "campus": "all"
    },
    "02_SPOKES_AUDIT": {
        "clearance": "staff",
        "category": "audit",
        "classification": "INTERNAL - AUDIT INSTRUMENT",
        "purview_label": "Internal - Educational",
        "allowed_roles": ["staff", "counselor", "admin"],
        "campus": "all"
    },
    "03_SPOKES_AUDIT_TECH": {
        "clearance": "staff",
        "category": "curriculum",
        "classification": "INTERNAL - ACADEMIC AUDIT",
        "purview_label": "Internal - Educational",
        "allowed_roles": ["staff", "counselor", "admin"],
        "campus": "all"
    }
}

DEFAULT_METADATA = {
    "clearance": "public",
    "category": "general",
    "classification": "PUBLIC - GENERAL",
    "purview_label": "Public / Educational",
    "allowed_roles": ["public", "staff", "counselor", "admin"],
    "campus": "all"
}

# ==============================================================================
# CONTENT-AWARE PURVIEW SENSITIVITY & ZERO-TRUST CLEARANCE CLASSIFIER
# Prevents under-classification (data leakage) and over-classification (retrieval starvation)
# ==============================================================================
_NRC_REGEX = re.compile(r'\b\d{6}/\d{2}/\d{1}\b')
_FINANCE_CURRENCY_REGEX = re.compile(r'\b(?:zmw|kwacha|k\d{2,}|\$\d+)\b', re.IGNORECASE)
_FINANCE_KEYWORDS_REGEX = re.compile(r'\b(?:budget|payroll|salary|bursar(?:y|ies)?|financial ledger|expenditure|fqm subsid(?:y|ies)|balance sheet|procurement ledger)\b', re.IGNORECASE)
_IT_SECRET_REGEX = re.compile(r'\b(?:AKIA[0-9A-Z]{16}|aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40})\b')
_PRIVATE_KEY_REGEX = re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', re.IGNORECASE)
_DB_CONN_REGEX = re.compile(r'\b(?:postgres(?:ql)?|mysql|mongodb|redis):\/\/[^\s]+', re.IGNORECASE)
_IT_KEYWORDS_REGEX = re.compile(r'\b(?:network topology|server configuration|api key repository|sast security rule|ssh private key|root password)\b', re.IGNORECASE)
_PUBLIC_SYLLABUS_REGEX = re.compile(r'\b(?:cambridge 0580|igcse syllabus|curriculum syllabus|academic calendar|public school announcement|statutory safeguard|statutory prohibition)\b', re.IGNORECASE)
_PASTORAL_SAFEGUARDING_REGEX = re.compile(r'\b(?:pastoral safeguarding|child protection case|welfare case|student disciplinary hearing|counseling record)\b', re.IGNORECASE)

def classify_document_content(
    filename: str,
    clean_title: str,
    sections: List[Dict[str, Any]],
    folder: str
) -> Dict[str, Any]:
    """
    Performs content-aware scanning of document headings, paragraphs, and tables
    to derive accurate Purview Sensitivity Containers and Zero-Trust RBAC clearance tiers.
    Prevents under-classification (data leaks) and over-classification (retrieval starvation).
    """
    # Start with folder metadata or default
    meta = FOLDER_METADATA_MAP.get(folder, DEFAULT_METADATA).copy()

    # Aggregate text for analysis
    all_text = f"{filename} {clean_title} " + " ".join(
        f"{s.get('heading', '')} {s.get('content', '')}" for s in sections
    )
    lower_text = all_text.lower()
    fn_lower = filename.lower()

    # 1. Check for Restricted - IT / Systems (Highest restriction)
    if (
        _IT_SECRET_REGEX.search(all_text)
        or _PRIVATE_KEY_REGEX.search(all_text)
        or _DB_CONN_REGEX.search(all_text)
        or _IT_KEYWORDS_REGEX.search(lower_text)
        or "devops" in fn_lower
        or "topology" in fn_lower
    ):
        meta["clearance"] = "devops"
        meta["purview_label"] = "Restricted - IT / Systems"
        meta["category"] = "it_systems"
        meta["classification"] = "RESTRICTED - IT / SYSTEMS"
        meta["allowed_roles"] = ["devops", "admin"]
        return meta

    # 2. Check for Pastoral Safeguarding / Child Welfare (Counselor + Admin)
    if _PASTORAL_SAFEGUARDING_REGEX.search(lower_text) or "pastoral" in fn_lower or "safeguard" in fn_lower:
        meta["clearance"] = "counselor"
        meta["purview_label"] = "Confidential - Admin / Finance"
        meta["category"] = "pastoral"
        meta["classification"] = "CONFIDENTIAL - PASTORAL WELFARE"
        meta["allowed_roles"] = ["counselor", "admin"]
        return meta

    # 3. Check for Confidential - Admin / Finance
    # Zambian NRC numbers, currency figures, budget, payroll, bursary, action-plan
    has_nrc = bool(_NRC_REGEX.search(all_text))
    has_currency = bool(_FINANCE_CURRENCY_REGEX.search(all_text))
    has_fin_kw = bool(_FINANCE_KEYWORDS_REGEX.search(lower_text))
    has_admin_kw = bool(re.search(r'\b(action-plan|executive board|disciplinary|board paper|legal contract)\b', lower_text))

    if has_nrc or (has_currency and has_fin_kw) or has_admin_kw or "action-plan" in fn_lower or "finance" in fn_lower:
        meta["clearance"] = "admin"
        meta["purview_label"] = "Confidential - Admin / Finance"
        meta["category"] = "finance" if (has_currency or has_fin_kw) else "governance"
        meta["classification"] = "CONFIDENTIAL - ADMIN / FINANCE"
        meta["allowed_roles"] = ["admin", "finance"] if (has_currency or has_fin_kw) else ["admin"]
        return meta

    # 4. Check for Public / Educational (Syllabi, Public Announcements, Statutory Safeguards)
    if (
        _PUBLIC_SYLLABUS_REGEX.search(lower_text)
        or "public" in fn_lower
        or "syllabus" in fn_lower
        or "calendar" in fn_lower
    ):
        meta["clearance"] = "public"
        meta["purview_label"] = "Public / Educational"
        meta["category"] = "curriculum" if "syllabus" in lower_text or "cambridge" in lower_text else "governance"
        meta["classification"] = "PUBLIC - EDUCATIONAL"
        meta["allowed_roles"] = ["public", "staff", "counselor", "admin"]
        return meta

    # 5. Specific filename overrides (e.g. audit surveys, bypass curriculum)
    if "survey" in fn_lower:
        meta["clearance"] = "staff"
        meta["category"] = "audit"
        meta["classification"] = "INTERNAL - AUDIT INSTRUMENT"
        meta["purview_label"] = "Internal - Educational"
    elif "bypass" in fn_lower:
        meta["clearance"] = "staff"
        meta["category"] = "curriculum"
        meta["classification"] = "INTERNAL - ACADEMIC INTEGRITY"
        meta["purview_label"] = "Internal - Educational"

    # 6. Format-specific classification heuristics
    # Excel spreadsheets with financial keywords auto-escalate to admin clearance
    if fn_lower.endswith((".xlsx", ".xls")):
        if has_currency or has_fin_kw or "finance" in fn_lower or "budget" in fn_lower:
            meta["clearance"] = "admin"
            meta["purview_label"] = "Confidential - Admin / Finance"
            meta["category"] = "finance"
            meta["classification"] = "CONFIDENTIAL - ADMIN / FINANCE"
            meta["allowed_roles"] = ["admin", "finance"]
            return meta
        # Academic records in spreadsheet form
        _GRADES_REGEX = re.compile(r'\b(?:grades|marks|results|scores|assessment)\b', re.IGNORECASE)
        if _GRADES_REGEX.search(lower_text) or any(
            kw in fn_lower for kw in ("grades", "marks", "results", "scores")
        ):
            meta["clearance"] = "staff"
            meta["category"] = "academic"
            meta["classification"] = "INTERNAL - ACADEMIC RECORDS"
            meta["purview_label"] = "Internal - Educational"
            meta["allowed_roles"] = ["staff", "counselor", "admin"]

    # PDF documents with examination content
    if fn_lower.endswith(".pdf"):
        _EXAM_REGEX = re.compile(r'\b(?:exam(?:ination)?|test\s+paper|assessment\s+paper|question\s+paper|answer\s+key)\b', re.IGNORECASE)
        if _EXAM_REGEX.search(lower_text) or any(
            kw in fn_lower for kw in ("exam", "paper", "assessment", "question")
        ):
            meta["clearance"] = "staff"
            meta["category"] = "examination"
            meta["classification"] = "CONFIDENTIAL - EXAMINATION"
            meta["purview_label"] = "Confidential - Examination"
            meta["allowed_roles"] = ["staff", "admin"]

    return meta



def compute_file_sha256(file_path: str) -> str:
    """Computes the SHA-256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_docx_structured(file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Parses a .docx file and returns its document title and structured sections
    (paragraphs and tables grouped logically by headings).
    """
    doc = docx.Document(file_path)
    filename = os.path.splitext(os.path.basename(file_path))[0]
    clean_title = filename.replace("-", " ").replace("_", " ").title()

    sections: List[Dict[str, Any]] = []
    current_heading = clean_title
    current_paragraphs: List[str] = []

    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue

        # Detect heading styles or short emphasized lines
        is_heading = (
            p.style.name.startswith("Heading") or
            p.style.name in ["Title", "Subtitle"] or
            (len(txt) < 80 and txt.isupper()) or
            (len(txt) < 100 and (txt.startswith("Section ") or txt.startswith("Part ") or txt.startswith("Guardrail ")))
        )

        if is_heading:
            if current_paragraphs:
                sections.append({
                    "heading": current_heading,
                    "content": "\n".join(current_paragraphs)
                })
                current_paragraphs = []
            current_heading = txt
        else:
            current_paragraphs.append(txt)

    if current_paragraphs:
        sections.append({
            "heading": current_heading,
            "content": "\n".join(current_paragraphs)
        })

    # Also capture tables as structured text
    for t_idx, t in enumerate(doc.tables, 1):
        table_rows = []
        for row in t.rows:
            row_cells = [c.text.strip().replace("\n", " ") for c in row.cells]
            if any(row_cells):
                table_rows.append(" | ".join(row_cells))
        if table_rows:
            sections.append({
                "heading": f"{clean_title} - Table {t_idx}",
                "content": "TABLE DATA:\n" + "\n".join(table_rows)
            })

    # If no headings were found and everything ended up in one section or empty
    if not sections:
        all_paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        if all_paras:
            sections.append({
                "heading": clean_title,
                "content": "\n".join(all_paras)
            })

    return clean_title, sections


def chunk_section(
    title: str,
    heading: str,
    text: str,
    doc_prefix: str,
    max_chunk_chars: int = 1500,
    overlap_chars: int = 200
) -> List[Dict[str, str]]:
    """
    Splits text into chunks preserving heading context and sentence boundaries.
    """
    if len(text) <= max_chunk_chars:
        return [{
            "sub_id": "001",
            "title": f"{title}: {heading}" if heading and heading != title else title,
            "content": f"{heading.upper()}:\n{text}" if heading and not text.startswith(heading) else text
        }]

    # Split into paragraphs first
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    current_chunk = []
    current_len = 0
    chunk_num = 1

    for p in paragraphs:
        if current_len + len(p) > max_chunk_chars and current_chunk:
            combined = "\n".join(current_chunk)
            chunks.append({
                "sub_id": f"{chunk_num:03d}",
                "title": f"{title}: {heading} (Part {chunk_num})",
                "content": f"{heading.upper()}:\n{combined}"
            })
            chunk_num += 1
            # Maintain brief overlap
            overlap = current_chunk[-1] if len(current_chunk[-1]) < overlap_chars else ""
            current_chunk = [overlap, p] if overlap else [p]
            current_len = sum(len(x) for x in current_chunk)
        else:
            current_chunk.append(p)
            current_len += len(p)

    if current_chunk:
        combined = "\n".join(current_chunk)
        chunks.append({
            "sub_id": f"{chunk_num:03d}",
            "title": f"{title}: {heading} (Part {chunk_num})" if chunk_num > 1 else f"{title}: {heading}",
            "content": f"{heading.upper()}:\n{combined}"
        })

    return chunks


class FrameworkSyncService:
    """
    Monitors configured directory/directories for document modifications (.docx, .pdf, .xlsx/.xls),
    computes SHA-256 diffs, and produces incremental records for the vector store.
    """

    def __init__(
        self,
        framework_dir: Optional[Union[str, List[str]]] = None,
        state_file: str = STATE_PATH,
        data_file: str = DATA_PATH
    ):
        self.watch_dirs = resolve_watch_dirs(framework_dir)
        self.framework_dir = self.watch_dirs[0] if self.watch_dirs else os.path.join(BASE_DIR, "EDUCORE_AI_FRAMEWORK")
        self.state_file = state_file
        self.data_file = data_file
        self._ensure_paths()
        TELEMETRY.set_watch_dirs_count(len(self.watch_dirs))

    def _ensure_paths(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)

    def load_state(self) -> Dict[str, Any]:
        """Loads sync state tracking file hashes and chunk IDs."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"files": {}, "last_sync_time": 0, "total_chunks": 0}

    def save_state(self, state: Dict[str, Any]):
        """Persists the sync state to disk atomically."""
        tmp = self.state_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.state_file)

    def scan_framework_files(self) -> Dict[str, Dict[str, Any]]:
        """
        Discovers all supported document files (.docx, .pdf, .xlsx, .xls) across
        all configured watch directories, ignoring temporary/lock files.
        Returns a map of relative_path -> {full_path, hash, mtime, folder, filename, watch_dir}.
        """
        results = {}
        multiple_dirs = len(self.watch_dirs) > 1

        for w_dir in self.watch_dirs:
            if not os.path.exists(w_dir):
                continue

            dir_prefix = os.path.basename(w_dir.rstrip("\\/")) if multiple_dirs else ""

            for root, _, files in os.walk(w_dir):
                for fname in sorted(files):
                    # Check against supported extensions registry
                    ext = os.path.splitext(fname)[1].lower()
                    if ext not in SUPPORTED_EXTENSIONS:
                        continue
                    if fname.startswith("~$") or fname.startswith("."):
                        continue  # Ignore MS Office temporary locks

                    full_path = os.path.join(root, fname)
                    sub_rel = os.path.relpath(full_path, w_dir).replace("\\", "/")
                    rel_path = f"{dir_prefix}/{sub_rel}".lstrip("/") if dir_prefix else sub_rel
                    
                    # Determine containing folder
                    parts = sub_rel.split("/")
                    folder = parts[0] if len(parts) > 1 else "ROOT"

                    try:
                        file_hash = compute_file_sha256(full_path)
                        mtime = os.path.getmtime(full_path)
                        results[rel_path] = {
                            "full_path": full_path,
                            "rel_path": rel_path,
                            "hash": file_hash,
                            "mtime": mtime,
                            "folder": folder,
                            "filename": fname,
                            "watch_dir": w_dir
                        }
                    except Exception as err:
                        print(f"[SyncService] Warning reading {rel_path}: {err}")

        return results

    def parse_file_to_records(self, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses a document file into structured corpus records with Purview & RBAC metadata.
        Supports all formats registered in the document_readers module.
        """
        full_path = file_info["full_path"]
        folder = file_info["folder"]
        rel_path = file_info["rel_path"]

        clean_title, sections = read_document(full_path)

        # Content-aware Purview sensitivity and RBAC metadata classification
        meta = classify_document_content(file_info["filename"], clean_title, sections, folder)

        # Format-aware chunk ID prefix for traceability
        format_prefix = get_format_prefix(full_path)
        # Strip any known extension for the slug
        fname_base = file_info["filename"]
        for ext in SUPPORTED_EXTENSIONS:
            if fname_base.lower().endswith(ext):
                fname_base = fname_base[:len(fname_base) - len(ext)]
                break
        doc_slug = re.sub(r'[^a-zA-Z0-9]+', '-', fname_base).strip("-").upper()
        doc_prefix = f"{format_prefix}-{doc_slug[:20]}"

        records = []

        sec_idx = 1
        for sec in sections:
            heading = sec.get("heading", "")
            content = sec.get("content", "").strip()
            if not content:
                continue

            chunks = chunk_section(clean_title, heading, content, doc_prefix)
            for c in chunks:
                chunk_id = f"{doc_prefix}-S{sec_idx:02d}-{c['sub_id']}"
                records.append({
                    "id": chunk_id,
                    "title": c["title"],
                    "content": c["content"],
                    "campus": meta.get("campus", "all"),
                    "clearance": meta.get("clearance", "staff"),
                    "category": meta.get("category", "governance"),
                    "classification": meta.get("classification", "INTERNAL"),
                    "purview_label": meta.get("purview_label", "Internal - Educational"),
                    "allowed_roles": meta.get("allowed_roles", ["staff", "admin"]),
                    "source_file": rel_path
                })
            sec_idx += 1

        return records

    def detect_changes(self, force: bool = False) -> Dict[str, Any]:
        """
        Compares current filesystem against the recorded state.
        Returns:
            {
                "changed": bool,
                "added_files": List[str],
                "modified_files": List[str],
                "deleted_files": List[str],
                "current_files": Dict[str, Dict[str, Any]]
            }
        """
        state = self.load_state()
        known_files = state.get("files", {})
        current_files = self.scan_framework_files()

        added = []
        modified = []
        deleted = []

        for rel_path, c_info in current_files.items():
            if rel_path not in known_files or force:
                added.append(rel_path)
            elif known_files[rel_path].get("hash") != c_info["hash"]:
                modified.append(rel_path)

        for rel_path in known_files:
            if rel_path not in current_files:
                deleted.append(rel_path)

        has_changes = bool(added or modified or deleted)
        return {
            "changed": has_changes,
            "added_files": added,
            "modified_files": modified,
            "deleted_files": deleted,
            "current_files": current_files,
            "known_files": known_files
        }

    def generate_incremental_update(self, force: bool = False) -> Dict[str, Any]:
        """
        Calculates the delta (new/modified records and deleted chunk IDs)
        and updates the persistent sync state and enterprise_data.json.
        """
        t0 = time.time()
        diff = self.detect_changes(force=force)

        if not diff["changed"] and not force:
            return {
                "changed": False,
                "records_to_upsert": [],
                "ids_to_delete": [],
                "updated_files": [],
                "duration_ms": round((time.time() - t0) * 1000, 2)
            }

        state = self.load_state()
        known_files = state.get("files", {})
        current_files = diff["current_files"]

        records_to_upsert = []
        ids_to_delete = []
        updated_files = diff["added_files"] + diff["modified_files"]

        # Handle deleted files
        for rel_path in diff["deleted_files"]:
            old_chunk_ids = known_files.get(rel_path, {}).get("chunk_ids", [])
            ids_to_delete.extend(old_chunk_ids)
            if rel_path in known_files:
                del known_files[rel_path]

        # Handle modified files (evict old chunk IDs first)
        for rel_path in diff["modified_files"]:
            old_chunk_ids = known_files.get(rel_path, {}).get("chunk_ids", [])
            ids_to_delete.extend(old_chunk_ids)

        # Parse added & modified files
        t_parse_start = time.time()
        for rel_path in updated_files:
            c_info = current_files[rel_path]
            file_records = self.parse_file_to_records(c_info)
            print(f"[Parser] Extracted {len(file_records)} chunk(s) from '{rel_path}' (SHA-256: {c_info['hash'][:10]}...)")
            records_to_upsert.extend(file_records)

            # Record new chunk IDs in state
            known_files[rel_path] = {
                "hash": c_info["hash"],
                "mtime": c_info["mtime"],
                "chunk_ids": [r["id"] for r in file_records],
                "chunk_count": len(file_records),
                "last_synced": time.time()
            }

        parse_duration_ms = round((time.time() - t_parse_start) * 1000, 2) if updated_files else 0.0
        if updated_files:
            TELEMETRY.record_batch_parse(updated_files, parse_duration_ms, len(records_to_upsert))

        # Deduplicate ids_to_delete vs records_to_upsert
        upsert_ids = {r["id"] for r in records_to_upsert}
        final_delete_ids = [cid for cid in ids_to_delete if cid not in upsert_ids]

        # Update persistent enterprise_data.json
        self._update_enterprise_data(records_to_upsert, final_delete_ids)

        # Save state
        total_chunks = sum(f.get("chunk_count", 0) for f in known_files.values())
        state["files"] = known_files
        state["last_sync_time"] = time.time()
        state["total_chunks"] = total_chunks
        self.save_state(state)

        duration = round((time.time() - t0) * 1000, 2)
        return {
            "changed": True,
            "records_to_upsert": records_to_upsert,
            "ids_to_delete": final_delete_ids,
            "updated_files": updated_files,
            "deleted_files": diff["deleted_files"],
            "total_chunks": total_chunks,
            "parse_duration_ms": parse_duration_ms,
            "duration_ms": duration
        }

    def _update_enterprise_data(self, upsert_records: List[Dict[str, Any]], delete_ids: List[str]):
        """Synchronizes enterprise_data.json with the incremental changes."""
        existing = []
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        delete_set = set(delete_ids)
        upsert_map = {r["id"]: r for r in upsert_records}

        # Keep records not in delete_set and not being replaced
        updated = [r for r in existing if r.get("id") not in delete_set and r.get("id") not in upsert_map]

        # Append new/replaced records
        updated.extend(upsert_records)

        # Atomic write
        tmp = self.data_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.data_file)
