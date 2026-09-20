from __future__ import annotations

import re

from app.agents.utils import evidence, first_match, is_heading, sentences
from app.schemas.contracts import CitedValue, ContractOverview
from app.services.document_service import DocumentChunk


DATE = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\d{4}-\d{2}-\d{2}"


class ContractAgent:
    def analyze(self, chunks: list[DocumentChunk]) -> ContractOverview:
        overview = ContractOverview()
        party_match = first_match(chunks, r"(?:by and between|between)\s+(.{3,180}?)\s+(?:and|,?\s+and)\s+(.{3,180}?)(?:[.;\n]|\s+\()")
        if party_match:
            chunk, snippet = party_match
            match = re.search(r"(?:by and between|between)\s+(.{3,180}?)\s+(?:and|,?\s+and)\s+(.{3,180}?)(?:[.;\n]|\s+\()", snippet, re.I | re.DOTALL)
            if match:
                parties: list[CitedValue] = []
                for val in match.groups():
                    cleaned = re.sub(r"\s*\([^)]*\)", "", val).strip(" ,;\n\t\r")
                    if cleaned.endswith(".") and not re.search(r"\b(?:Inc|LLC|Ltd|Corp|Co)\.$", cleaned, re.I):
                        cleaned = cleaned[:-1].strip()
                    if cleaned:
                        parties.append(CitedValue(value=cleaned, evidence=evidence(chunk, snippet)))
                overview.parties = parties

        fields = (
            ("effective_date", r"(?:effective\s+(?:as\s+of|date(?:\s+is)?)[^.!\n]{0,100}?)(" + DATE + r")"),
            ("expiration_date", r"(?:expire(?:s|d|ation)?(?:\s+on|\s+date(?:\s+is)?)[^.!\n]{0,100}?)(" + DATE + r")"),
        )
        for name, pattern in fields:
            for chunk in chunks:
                found = False
                for sentence in sentences(chunk):
                    date_match = re.search(pattern, sentence, re.I)
                    if date_match:
                        raw_date = re.search(DATE, date_match.group(0), re.I)
                        if raw_date:
                            setattr(overview, name, CitedValue(value=raw_date.group(0), evidence=evidence(chunk, sentence)))
                            found = True
                            break
                if found:
                    break

        buckets = {
            "renewal_terms": r"\b(?:renew(?:al|s|ed|ing)|automatically renew)\b",
            "payment_terms": r"\b(?:payment|invoice|fee|fees|amount due|late payment)\b",
            "termination_terms": r"\b(?:terminate|termination|notice period)\b",
            "important_terms": r"\b(?:confidential|service level|data protection|report(?:ing)?|deliverable)\b",
        }
        for target, pattern in buckets.items():
            values: list[CitedValue] = []
            for chunk in chunks:
                for sentence in sentences(chunk):
                    if is_heading(sentence) or len(sentence) < 20:
                        continue
                    if re.search(pattern, sentence, re.I):
                        if any(v.value == sentence for v in values):
                            continue
                        values.append(CitedValue(value=sentence, evidence=evidence(chunk, sentence)))
                        if len(values) == 5:
                            break
                if len(values) == 5:
                    break
            setattr(overview, target, values)
        return overview
