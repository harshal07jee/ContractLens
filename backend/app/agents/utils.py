from __future__ import annotations

import re

from app.schemas.contracts import Evidence
from app.services.document_service import DocumentChunk, SECTION_PATTERN


def is_heading(text: str) -> bool:
    cleaned = text.strip()
    if not cleaned:
        return False
    if SECTION_PATTERN.match(cleaned):
        return True
    if len(cleaned) < 50 and cleaned.isupper():
        return True
    return False


SENTENCE_SPLIT_PATTERN = re.compile(
    r"(?<!\bInc)(?<!\bLtd)(?<!\bCorp)(?<!\bCo)(?<!\bNo)(?<!\bSec)(?<!\be\.g)(?<!\bi\.e)(?<!\bvs)(?<=[.!?])\s+(?=[A-Z0-9])"
)


def sentences(chunk: DocumentChunk) -> list[str]:
    results: list[str] = []
    for paragraph in re.split(r"\n+", chunk.text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        splits = [s.strip() for s in SENTENCE_SPLIT_PATTERN.split(paragraph) if s.strip()]
        results.extend(splits)
    return results


def evidence(chunk: DocumentChunk, text: str) -> Evidence:
    return Evidence(
        source_id=chunk.source_id,
        chunk_id=chunk.chunk_id or str(chunk.ordinal),
        page=chunk.page,
        section=chunk.section,
        excerpt=text[:1_000],
    )


def first_match(chunks: list[DocumentChunk], pattern: str) -> tuple[DocumentChunk, str] | None:
    regex = re.compile(pattern, re.IGNORECASE | re.DOTALL)
    for chunk in chunks:
        match = regex.search(chunk.text)
        if match:
            return chunk, match.group(0).strip()
    return None
