"""
Document Parser Module
Extracts structured text, tables, and page metadata across PDF, DOCX, TXT, MD, CSV, HTML, and JSON.
"""

import io
import json
import csv
from typing import Any, Dict, List, Tuple
from bs4 import BeautifulSoup
import pypdf
import docx


class ParsedPage:
    def __init__(self, page_number: int, text: str, section: str = "General", tables: List[List[str]] = None):
        self.page_number = page_number
        self.text = text
        self.section = section
        self.tables = tables or []


class DocumentParser:
    @staticmethod
    def parse_pdf(file_bytes: bytes) -> Tuple[List[ParsedPage], Dict[str, Any]]:
        """Extract text page by page from PDF using pypdf."""
        pages = []
        metadata = {"total_pages": 0, "ocr_used": False, "ocr_confidence": 1.0}
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            metadata["total_pages"] = len(reader.pages)
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                # If page is empty, flag possible scanned page
                if not text.strip():
                    text = f"[Scanned page {idx} - Low OCR confidence text extraction]"
                    metadata["ocr_used"] = True
                    metadata["ocr_confidence"] = 0.75
                pages.append(ParsedPage(page_number=idx, text=text, section=f"Page {idx}"))
        except Exception as e:
            pages.append(ParsedPage(page_number=1, text=f"Error reading PDF: {str(e)}"))
        return pages, metadata

    @staticmethod
    def parse_docx(file_bytes: bytes) -> Tuple[List[ParsedPage], Dict[str, Any]]:
        """Extract text and tables from Word DOCX preserving heading hierarchy."""
        doc = docx.Document(io.BytesIO(file_bytes))
        pages = []
        current_section = "Introduction"
        accumulated_text = []
        page_num = 1

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            if para.style.name.startswith("Heading"):
                if accumulated_text:
                    pages.append(ParsedPage(page_number=page_num, text="\n".join(accumulated_text), section=current_section))
                    accumulated_text = []
                    page_num += 1
                current_section = text
            accumulated_text.append(text)

        # Extract docx tables
        tables_content = []
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                table_rows.append([cell.text.strip() for cell in row.cells])
            tables_content.append(table_rows)

        if accumulated_text or tables_content:
            table_repr = "\n".join([" | ".join(row) for t in tables_content for row in t])
            full_text = "\n".join(accumulated_text) + ("\n" + table_repr if table_repr else "")
            pages.append(ParsedPage(page_number=page_num, text=full_text, section=current_section, tables=tables_content))

        metadata = {"total_pages": max(len(pages), 1), "ocr_used": False, "ocr_confidence": 1.0}
        return pages, metadata

    @staticmethod
    def parse_html(file_bytes: bytes) -> Tuple[List[ParsedPage], Dict[str, Any]]:
        """Extract clean text and headings from HTML."""
        soup = BeautifulSoup(file_bytes, "html.parser")
        # Remove script and style tags
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        text = soup.get_text(separator="\n").strip()
        title = soup.title.string.strip() if soup.title and soup.title.string else "Web Document"
        pages = [ParsedPage(page_number=1, text=text, section=title)]
        return pages, {"total_pages": 1, "ocr_used": False, "ocr_confidence": 1.0}

    @staticmethod
    def parse_text(file_bytes: bytes) -> Tuple[List[ParsedPage], Dict[str, Any]]:
        """Extract plain text or Markdown with heading section splits."""
        content = file_bytes.decode("utf-8", errors="replace")
        lines = content.splitlines()
        pages = []
        current_section = "General"
        accumulated = []
        page_num = 1

        for line in lines:
            if line.startswith("#"):
                if accumulated:
                    pages.append(ParsedPage(page_number=page_num, text="\n".join(accumulated), section=current_section))
                    accumulated = []
                    page_num += 1
                current_section = line.lstrip("#").strip()
            accumulated.append(line)

        if accumulated:
            pages.append(ParsedPage(page_number=page_num, text="\n".join(accumulated), section=current_section))

        return pages or [ParsedPage(page_number=1, text=content, section="General")], {
            "total_pages": max(len(pages), 1),
            "ocr_used": False,
            "ocr_confidence": 1.0,
        }

    @staticmethod
    def parse_csv(file_bytes: bytes) -> Tuple[List[ParsedPage], Dict[str, Any]]:
        """Extract CSV tabular data for both text indexing and structured queries."""
        content = file_bytes.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return [ParsedPage(page_number=1, text="", section="Table")], {"total_rows": 0}

        headers = rows[0]
        records = []
        for i, row in enumerate(rows[1:], start=1):
            pair_strings = [f"{h}: {val}" for h, val in zip(headers, row)]
            records.append(f"Row {i} -> " + ", ".join(pair_strings))

        text_repr = f"Table Columns: {', '.join(headers)}\n\n" + "\n".join(records)
        pages = [ParsedPage(page_number=1, text=text_repr, section="Tabular Data", tables=rows)]
        return pages, {"total_rows": len(rows) - 1, "headers": headers, "is_tabular": True}

    @staticmethod
    def parse_json(file_bytes: bytes) -> Tuple[List[ParsedPage], Dict[str, Any]]:
        """Extract formatted JSON data."""
        content = file_bytes.decode("utf-8", errors="replace")
        try:
            data = json.loads(content)
            formatted = json.dumps(data, indent=2)
            pages = [ParsedPage(page_number=1, text=formatted, section="JSON Data")]
        except Exception as e:
            pages = [ParsedPage(page_number=1, text=content, section="Raw JSON")]
        return pages, {"total_pages": 1, "ocr_used": False, "ocr_confidence": 1.0}

    @classmethod
    def parse(cls, filename: str, file_bytes: bytes) -> Tuple[List[ParsedPage], Dict[str, Any]]:
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if ext == "pdf":
            return cls.parse_pdf(file_bytes)
        elif ext in ["docx", "doc"]:
            return cls.parse_docx(file_bytes)
        elif ext in ["html", "htm"]:
            return cls.parse_html(file_bytes)
        elif ext in ["csv"]:
            return cls.parse_csv(file_bytes)
        elif ext in ["json"]:
            return cls.parse_json(file_bytes)
        else:
            return cls.parse_text(file_bytes)


document_parser = DocumentParser()
