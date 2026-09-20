from __future__ import annotations

import re

from app.agents.utils import evidence, is_heading, sentences
from app.schemas.contracts import Obligation
from app.services.document_service import DocumentChunk


OBLIGATION_PATTERN = re.compile(r"\b(?:shall|must|agrees? to|is required to|will)\b", re.I)
FREQUENCY_PATTERN = re.compile(r"\b(?:daily|weekly|monthly|quarterly|annually|each\s+(?:month|quarter|year))\b", re.I)
DEADLINE_PATTERN = re.compile(r"\b(?:within\s+\d+\s+(?:business\s+)?days?(?:\s+after\s+[^.;]+)?|no later than[^.;]+|by\s+[A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b", re.I)
PARTY_PATTERN = re.compile(r"^\s*([A-Z][A-Za-z0-9 &,.()-]{1,80}?)\s+(?:shall|must|agrees? to|is required to|will)\b", re.I)
NON_PARTY_SUBJECTS = {"this agreement", "agreement", "the agreement", "contract", "the contract"}


class ObligationAgent:
    def extract(self, chunks: list[DocumentChunk]) -> list[Obligation]:
        obligations: list[Obligation] = []
        seen: set[str] = set()
        for chunk in chunks:
            for sentence in sentences(chunk):
                if is_heading(sentence) or len(sentence) < 20:
                    continue
                if not OBLIGATION_PATTERN.search(sentence):
                    continue
                normalized = " ".join(sentence.lower().split())
                if normalized in seen:
                    continue
                seen.add(normalized)
                party_match = PARTY_PATTERN.search(sentence)
                party_name = party_match.group(1).strip(" ,") if party_match else None
                if party_name and party_name.lower() in NON_PARTY_SUBJECTS:
                    continue
                if party_name and party_name.lower() in {"each report", "report"}:
                    party_name = "Vendor (Reporting)"
                frequency = FREQUENCY_PATTERN.search(sentence)
                deadline = DEADLINE_PATTERN.search(sentence)
                obligations.append(Obligation(
                    party=party_name,
                    description=sentence,
                    frequency=frequency.group(0) if frequency else None,
                    deadline=deadline.group(0).strip() if deadline else None,
                    evidence=evidence(chunk, sentence),
                ))
        return obligations
