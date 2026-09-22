# ==============================================================================
# EDUCORE ENTERPRISE - PLUGGABLE DOCUMENT READER ABSTRACTION LAYER
# Multi-format document extraction: DOCX, PDF, Excel (.xlsx/.xls)
# Compliance: ISO/IEC 42001:2023 | Zambian Data Protection Act No. 3 of 2021
# ==============================================================================
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import docx


# ==============================================================================
# ABSTRACT BASE CLASS
# ==============================================================================

class DocumentReader(ABC):
    """
    Base class for all document readers.
    Every reader must return a uniform (clean_title, sections) tuple where
    sections is a list of dicts with 'heading' and 'content' keys.
    """

    @abstractmethod
    def read(self, file_path: str, **kwargs) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse a file and return structured sections.

        Returns:
            (clean_title, sections) where sections = [{"heading": str, "content": str}, ...]
        """
        ...

    @staticmethod
    def _derive_clean_title(file_path: str) -> str:
        """Derives a human-readable title from a filename."""
        filename = os.path.splitext(os.path.basename(file_path))[0]
        return filename.replace("-", " ").replace("_", " ").title()


# ==============================================================================
# DOCX READER — Extracted from framework_sync_service.read_docx_structured()
# ==============================================================================

class DocxReader(DocumentReader):
    """
    Parses Microsoft Word .docx files using python-docx.
    Extracts paragraphs grouped by heading structure and tables as pipe-delimited text.
    """

    def read(self, file_path: str, **kwargs) -> Tuple[str, List[Dict[str, Any]]]:
        doc = docx.Document(file_path)
        clean_title = self._derive_clean_title(file_path)

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

        # Capture tables as structured text
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

        # Fallback: if no headings were found
        if not sections:
            all_paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            if all_paras:
                sections.append({
                    "heading": clean_title,
                    "content": "\n".join(all_paras)
                })

        return clean_title, sections


# ==============================================================================
# PDF READER — pypdfium2-based extraction (Zero Egress, 100% Offline)
# ==============================================================================

class PdfReader(DocumentReader):
    """
    Parses PDF files using pypdfium2 (PDFium engine).
    100% offline, zero-egress, and requires no external ML models or network access.
    Extracts text per page, detecting heading structures or falling back
    to page-level sections.
    """

    def read(self, file_path: str, **kwargs) -> Tuple[str, List[Dict[str, Any]]]:
        import pypdfium2 as pdfium

        clean_title = self._derive_clean_title(file_path)
        sections: List[Dict[str, Any]] = []

        with pdfium.PdfDocument(file_path) as pdf:
            total_pages = len(pdf)
            page_range = kwargs.get("page_range")
            start_page = (page_range[0] - 1) if page_range else 0
            end_page = min(page_range[1], total_pages) if page_range else total_pages

            for page_idx in range(start_page, end_page):
                page = pdf[page_idx]
                textpage = page.get_textpage()
                page_text = textpage.get_text_range().strip()
                if not page_text:
                    continue

                page_sections = self._extract_page_sections(page_text, clean_title, page_idx + 1)
                sections.extend(page_sections)

        if not sections:
            sections.append({
                "heading": clean_title,
                "content": f"[Empty PDF: {os.path.basename(file_path)}]"
            })

        return clean_title, sections

    @staticmethod
    def _extract_page_sections(page_text: str, clean_title: str, page_num: int) -> List[Dict[str, Any]]:
        """
        Splits page text into sections by detecting prominent heading lines,
        or groups under a page heading if no distinct headings are detected.
        """
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        if not lines:
            return []

        heading_regex = re.compile(
            r'^(?:(?:SECTION|PART|CHAPTER|ARTICLE|GUARDRAIL)\s+\d+[:\-\.]?.*|[A-Z0-9\s\-_:]{4,60})$'
        )

        sections: List[Dict[str, Any]] = []
        current_heading = f"{clean_title} - Page {page_num}"
        current_lines: List[str] = []

        for line in lines:
            is_heading = (
                (len(line) < 80 and line.isupper())
                or bool(heading_regex.match(line))
            ) and len(line) > 3

            if is_heading:
                if current_lines:
                    sections.append({
                        "heading": current_heading,
                        "content": "\n".join(current_lines)
                    })
                    current_lines = []
                current_heading = f"{clean_title} - {line}"
            else:
                current_lines.append(line)

        if current_lines:
            sections.append({
                "heading": current_heading,
                "content": "\n".join(current_lines)
            })

        return sections


# ==============================================================================
# EXCEL READER — openpyxl-based worksheet extraction with pipe-delimited rows
# ==============================================================================

class ExcelReader(DocumentReader):
    """
    Parses Excel .xlsx/.xls files using openpyxl.
    Each worksheet becomes a section. Rows are serialised as pipe-delimited text,
    matching the existing table format used for DOCX tables.
    """

    # Maximum rows per section chunk to prevent oversized sections
    MAX_ROWS_PER_SECTION = 200

    def read(self, file_path: str, **kwargs) -> Tuple[str, List[Dict[str, Any]]]:
        import openpyxl

        clean_title = self._derive_clean_title(file_path)

        # data_only=True resolves formulas to their computed values
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        except Exception:
            # Fallback without read_only for files that don't support it
            wb = openpyxl.load_workbook(file_path, data_only=True)

        sections: List[Dict[str, Any]] = []

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows_data = []

            for row in ws.iter_rows(values_only=True):
                # Convert each cell to string, handling None values
                cells = [str(cell).strip() if cell is not None else "" for cell in row]
                # Skip entirely empty rows
                if any(cells):
                    rows_data.append(" | ".join(cells))

            if not rows_data:
                continue  # Skip empty worksheets

            # Split into sub-sections if the sheet has too many rows
            if len(rows_data) <= self.MAX_ROWS_PER_SECTION:
                sections.append({
                    "heading": f"{clean_title} - {sheet_name}",
                    "content": "TABLE DATA:\n" + "\n".join(rows_data)
                })
            else:
                part = 1
                for start in range(0, len(rows_data), self.MAX_ROWS_PER_SECTION):
                    chunk = rows_data[start:start + self.MAX_ROWS_PER_SECTION]
                    sections.append({
                        "heading": f"{clean_title} - {sheet_name} (Part {part})",
                        "content": "TABLE DATA:\n" + "\n".join(chunk)
                    })
                    part += 1

        try:
            wb.close()
        except Exception:
            pass

        # Fallback: if workbook has no data at all
        if not sections:
            sections.append({
                "heading": clean_title,
                "content": f"[Empty workbook: {os.path.basename(file_path)}]"
            })

        return clean_title, sections


# ==============================================================================
# READER REGISTRY & FACTORY
# ==============================================================================

# Singleton reader instances (stateless, thread-safe for DocxReader & ExcelReader)
_DOCX_READER = DocxReader()
_PDF_READER = PdfReader()
_EXCEL_READER = ExcelReader()

# Extension -> Reader mapping
READER_REGISTRY: Dict[str, DocumentReader] = {
    ".docx": _DOCX_READER,
    ".pdf": _PDF_READER,
    ".xlsx": _EXCEL_READER,
    ".xls": _EXCEL_READER,
}

# Set of all supported file extensions
SUPPORTED_EXTENSIONS = frozenset(READER_REGISTRY.keys())

# Format hint prefixes for chunk ID generation
FORMAT_PREFIX_MAP: Dict[str, str] = {
    ".docx": "EDU-FW",
    ".pdf": "EDU-PDF",
    ".xlsx": "EDU-XLS",
    ".xls": "EDU-XLS",
}


def read_document(file_path: str, **kwargs) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Factory function: dispatches to the correct reader based on file extension.

    Args:
        file_path: Absolute or relative path to the document file.
        **kwargs: Additional keyword arguments passed to the reader.

    Returns:
        (clean_title, sections) tuple.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Document not found: {file_path}")

    ext = Path(file_path).suffix.lower()

    if ext not in READER_REGISTRY:
        raise ValueError(
            f"Unsupported file format '{ext}'. "
            f"Supported formats: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    reader = READER_REGISTRY[ext]
    return reader.read(file_path, **kwargs)


def get_format_prefix(file_path: str) -> str:
    """Returns the chunk ID prefix for a given file based on its format."""
    ext = Path(file_path).suffix.lower()
    return FORMAT_PREFIX_MAP.get(ext, "EDU-FW")
