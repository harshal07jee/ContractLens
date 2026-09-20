from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz


class DocumentProcessingError(ValueError):
    pass


@dataclass(frozen=True)
class PageText:
    page: int
    text: str


@dataclass(frozen=True)
class DocumentChunk:
    page: int
    section: str | None
    text: str
    ordinal: int
    source_id: str | None = None
    chunk_id: str | None = None


SECTION_PATTERN = re.compile(
    r"^[ \t]*(?:(\d+(?:\.\d+)*[.)]?[ \t]+[A-Za-z0-9][A-Za-z0-9 ,'\-]{1,80})|([A-Z][A-Z0-9 ,'\-]{2,60}))[ \t]*$"
)


def extract_pdf(path: Path) -> list[PageText]:
    try:
        document = fitz.open(path)
    except (fitz.FileDataError, RuntimeError) as exc:
        raise DocumentProcessingError("This file is not a readable PDF.") from exc
    try:
        pages: list[PageText] = []
        for index, page in enumerate(document):
            raw = page.get_text("text").strip()
            cleaned = reassemble_page_text(raw)
            if cleaned:
                pages.append(PageText(page=index + 1, text=cleaned))
    finally:
        document.close()
    if not pages or not any(page.text for page in pages):
        raise DocumentProcessingError("We couldn't extract readable text from this document. Please upload a text-readable PDF.")
    return pages


def reassemble_page_text(raw_text: str) -> str:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    cleaned_lines: list[str] = []
    for line in lines:
        if re.search(r"\|\s*Page\s+\d+$|^Page\s+\d+(\s+of\s+\d+)?$", line, re.I):
            continue
        cleaned_lines.append(line)

    paragraphs: list[str] = []
    current_para: list[str] = []
    for line in cleaned_lines:
        if SECTION_PATTERN.match(line):
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []
            paragraphs.append(line)
        else:
            current_para.append(line)
            if line.endswith((".", ":", "!", "?")):
                paragraphs.append(" ".join(current_para))
                current_para = []
    if current_para:
        paragraphs.append(" ".join(current_para))
    return "\n\n".join(paragraphs)


def detect_section(text: str) -> str | None:
    # First look for numbered sections (e.g. "1. PURPOSE")
    for line in text.splitlines():
        line = line.strip()
        match = SECTION_PATTERN.match(line)
        if match and match.group(1):
            return match.group(1).strip()
    # Otherwise return any matched uppercase heading
    for line in text.splitlines():
        line = line.strip()
        match = SECTION_PATTERN.match(line)
        if match:
            return (match.group(1) or match.group(2)).strip()
    return None


def chunk_pages(pages: list[PageText], contract_id: str = "", max_chars: int = 1_500) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for page in pages:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", page.text) if p.strip()]
        buffer = ""
        current_section = detect_section(page.text)
        for paragraph in paragraphs:
            para_section = detect_section(paragraph)
            if para_section:
                current_section = para_section
            if buffer and len(buffer) + len(paragraph) + 2 > max_chars:
                ordinal = len(chunks)
                chunk_src_id = f"{contract_id}-chunk-{ordinal}" if contract_id else f"chunk-{ordinal}"
                chunks.append(DocumentChunk(
                    page=page.page,
                    section=current_section,
                    text=buffer,
                    ordinal=ordinal,
                    source_id=chunk_src_id,
                    chunk_id=str(ordinal),
                ))
                buffer = ""
            buffer = f"{buffer}\n\n{paragraph}".strip()
        if buffer:
            ordinal = len(chunks)
            chunk_src_id = f"{contract_id}-chunk-{ordinal}" if contract_id else f"chunk-{ordinal}"
            chunks.append(DocumentChunk(
                page=page.page,
                section=current_section,
                text=buffer,
                ordinal=ordinal,
                source_id=chunk_src_id,
                chunk_id=str(ordinal),
            ))
    return chunks
