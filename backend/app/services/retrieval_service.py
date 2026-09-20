from __future__ import annotations

import re


TOKEN_PATTERN = re.compile(r"[a-z0-9]{2,}")
STOP_WORDS = {
    "a", "about", "after", "an", "and", "are", "as", "at", "be", "before", "by",
    "can", "could", "did", "do", "does", "for", "from", "have", "how", "if", "in",
    "into", "is", "me", "of", "on", "or", "so", "tell", "that", "the", "this",
    "to", "what", "when", "where", "which", "who", "with", "would", "should",
    "there", "their", "they", "your", "contract", "agreement",
}

SYNONYMS: dict[str, set[str]] = {
    "oblig": {"shall", "must", "will", "provid", "submit", "pay", "protect", "process", "requir"},
    "party": {"between", "vendor", "custom", "party", "enter"},
    "renew": {"renew", "success", "period", "notic"},
    "termin": {"termin", "breach", "cure", "conveni", "notic"},
    "pay": {"invoic", "fee", "arrear", "undisput", "interest"},
    "invoic": {"pay", "fee", "arrear", "undisput"},
    "date": {"effect", "expir", "term", "month", "year"},
    "expir": {"expir", "term", "end"},
}


def stem_token(t: str) -> str:
    if t.endswith("ies") and len(t) > 4:
        t = t[:-3] + "y"
    elif t.endswith("es") and len(t) > 4:
        t = t[:-2]
    elif t.endswith("s") and not t.endswith("ss") and len(t) > 3:
        t = t[:-1]

    if t.endswith("ation") and len(t) > 6:
        t = t[:-5]
    elif t.endswith("ated") and len(t) > 6:
        t = t[:-4]
    elif t.endswith("ate") and len(t) > 5:
        t = t[:-3]
    elif t.endswith("tion") and len(t) > 6:
        t = t[:-4]
    elif t.endswith("ing") and len(t) > 5:
        t = t[:-3]
    elif t.endswith("ed") and len(t) > 4:
        t = t[:-2]
    elif t.endswith("ment") and len(t) > 6:
        t = t[:-4]
    elif t.endswith("al") and len(t) > 5:
        t = t[:-2]

    if t.endswith("e") and len(t) > 3:
        t = t[:-1]
    return t


class RetrievalService:
    """Small, deterministic MVP retriever.

    SQLite remains the source of truth. This lexical retriever is intentionally isolated so a
    local embedding index can replace `retrieve` without changing the Q&A route or citations.
    """

    @staticmethod
    def _tokens(value: str) -> set[str]:
        tokens = set()
        for raw in TOKEN_PATTERN.findall(value.lower()):
            if raw in STOP_WORDS:
                continue
            stemmed = stem_token(raw)
            if stemmed not in STOP_WORDS and len(stemmed) >= 2:
                tokens.add(stemmed)
        return tokens

    def _expand_tokens(self, tokens: set[str]) -> set[str]:
        expanded = set(tokens)
        for token in tokens:
            for key, syns in SYNONYMS.items():
                if key in token or token in key:
                    expanded.update(syns)
        return expanded

    def retrieve(self, question: str, chunks: list[dict], limit: int = 3) -> list[dict]:
        query_tokens = self._tokens(question)
        if not query_tokens:
            return []
        expanded_query = self._expand_tokens(query_tokens)
        scored: list[tuple[int, int, dict]] = []
        for chunk in chunks:
            text_tokens = self._tokens(chunk["text"])
            exact_overlap = query_tokens & text_tokens
            expanded_overlap = expanded_query & text_tokens
            if exact_overlap or expanded_overlap:
                # Prioritize exact token overlap, then expanded overlap
                score = len(exact_overlap) * 3 + len(expanded_overlap)
                scored.append((score, len(expanded_overlap), chunk))
        return [
            chunk
            for _score, _exp, chunk in sorted(scored, key=lambda item: (-item[0], -item[1], item[2]["chunk_ordinal"]))[:limit]
        ]
