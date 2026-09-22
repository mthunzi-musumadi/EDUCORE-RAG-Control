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
from typing import Dict, Any, List, Tuple, Optional
import docx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMEWORK_DIR = os.path.join(BASE_DIR, "EDUCORE_AI_FRAMEWORK")
DATA_PATH = os.path.join(BASE_DIR, "production_setup", "enterprise_data.json")
STATE_PATH = os.path.join(BASE_DIR, "production_setup", "corpus_sync_state.json")

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
    "clearance": "staff",
    "category": "governance",
    "classification": "INTERNAL - GOVERNANCE POLICY",
    "purview_label": "Internal - Educational",
    "allowed_roles": ["staff", "counselor", "admin"],
    "campus": "all"
}


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
    Monitors EDUCORE_AI_FRAMEWORK for .docx modifications, computes SHA-256 diffs,
    and produces incremental records for the vector store.
    """

    def __init__(
        self,
        framework_dir: str = FRAMEWORK_DIR,
        state_file: str = STATE_PATH,
        data_file: str = DATA_PATH
    ):
        self.framework_dir = framework_dir
        self.state_file = state_file
        self.data_file = data_file
        self._ensure_paths()

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
        Discovers all .docx files in EDUCORE_AI_FRAMEWORK,
        ignoring Word lock/temp files (starting with ~$ or .).
        Returns a map of relative_path -> {full_path, hash, mtime, folder}.
        """
        results = {}
        if not os.path.exists(self.framework_dir):
            return results

        for root, _, files in os.walk(self.framework_dir):
            for fname in sorted(files):
                if not fname.lower().endswith(".docx"):
                    continue
                if fname.startswith("~$") or fname.startswith("."):
                    continue  # Ignore MS Word temporary locks

                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, self.framework_dir).replace("\\", "/")
                
                # Determine containing folder
                parts = rel_path.split("/")
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
                        "filename": fname
                    }
                except Exception as err:
                    print(f"[SyncService] Warning reading {rel_path}: {err}")

        return results

    def parse_file_to_records(self, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses a single .docx file into structured corpus records with Purview & RBAC metadata.
        """
        full_path = file_info["full_path"]
        folder = file_info["folder"]
        rel_path = file_info["rel_path"]

        # Derive metadata from folder or filename
        meta = FOLDER_METADATA_MAP.get(folder, DEFAULT_METADATA).copy()

        # Specific custom overrides for well-known framework documents
        fn_lower = file_info["filename"].lower()
        if "action-plan" in fn_lower:
            meta["clearance"] = "admin"
            meta["purview_label"] = "Confidential - Admin / Finance"
            meta["allowed_roles"] = ["admin"]
        elif "survey" in fn_lower:
            meta["clearance"] = "staff"
            meta["category"] = "audit"
        elif "bypass" in fn_lower:
            meta["clearance"] = "staff"
            meta["category"] = "curriculum"

        # Unique document prefix for chunk IDs
        doc_slug = re.sub(r'[^a-zA-Z0-9]+', '-', file_info["filename"].replace(".docx", "")).strip("-").upper()
        doc_prefix = f"EDU-FW-{doc_slug[:20]}"

        clean_title, sections = read_docx_structured(full_path)
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
        for rel_path in updated_files:
            c_info = current_files[rel_path]
            file_records = self.parse_file_to_records(c_info)
            records_to_upsert.extend(file_records)

            # Record new chunk IDs in state
            known_files[rel_path] = {
                "hash": c_info["hash"],
                "mtime": c_info["mtime"],
                "chunk_ids": [r["id"] for r in file_records],
                "chunk_count": len(file_records),
                "last_synced": time.time()
            }

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
