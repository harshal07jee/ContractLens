from __future__ import annotations

import re

from app.agents.contract_agent import DATE
from app.agents.utils import evidence, is_heading, sentences
from app.schemas.contracts import TimelineEvent
from app.services.document_service import DocumentChunk


RELATIVE = re.compile(
    r"\b(?:within|at least)\s+\d+\s+(?:business\s+)?days?\s+(?:after|before|of|prior to)[^.;]*|"
    r"\b\d+\s+(?:business\s+)?days?\s+(?:prior to|before|after|prior written notice)[^.;]*|"
    r"\bno later than[^.;]+",
    re.I
)
KEYWORDS = re.compile(r"\b(?:effective|expire|renew|payment|invoice|report|notice|terminate|milestone|deliver)\w*", re.I)


def make_title(sentence: str) -> str:
    s = sentence.lower()
    if "effective" in s:
        return "Effective date"
    if "renew" in s:
        return "Renewal notice deadline"
    if "expire" in s or "expiration" in s:
        return "Expiration date"
    if "cure" in s or ("breach" in s and "terminate" in s):
        return "Cure period deadline"
    if "convenience" in s and "terminate" in s:
        return "Termination for convenience notice"
    if "terminate" in s or "termination" in s:
        return "Termination notice deadline"
    if "invoice" in s or "payment" in s or "pay" in s:
        return "Payment deadline"
    if "report" in s:
        return "Reporting deadline"
    match = KEYWORDS.search(sentence)
    word = match.group(0).capitalize() if match else "Contract"
    return f"{word} deadline"


class TimelineAgent:
    def extract(self, chunks: list[DocumentChunk]) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        seen: set[tuple[str | None, str]] = set()
        for chunk in chunks:
            for sentence in sentences(chunk):
                if is_heading(sentence) or len(sentence) < 20:
                    continue
                if not KEYWORDS.search(sentence):
                    continue
                absolute = re.search(DATE, sentence, re.I)
                relative = RELATIVE.search(sentence)
                if not absolute and not relative:
                    continue
                date = absolute.group(0).strip() if absolute else None
                relation = relative.group(0).strip() if relative else None
                key = (date or relation, sentence.lower())
                if key in seen:
                    continue
                seen.add(key)
                title = make_title(sentence)
                events.append(TimelineEvent(
                    title=title,
                    date=date,
                    relative_deadline=relation,
                    description=sentence,
                    evidence=evidence(chunk, sentence),
                ))
        return events
