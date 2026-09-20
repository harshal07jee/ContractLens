from __future__ import annotations

import re

from app.agents.utils import is_heading, SENTENCE_SPLIT_PATTERN
from app.schemas.contracts import ChatAnswer, SourceCitation
from app.services.retrieval_service import RetrievalService


class QAAgent:
    def __init__(self, retrieval: RetrievalService) -> None:
        self.retrieval = retrieval

    def answer(self, question: str, chunks: list[dict]) -> ChatAnswer:
        matches = self.retrieval.retrieve(question, chunks)
        if not matches:
            return ChatAnswer(
                answer="I couldn't find sufficient evidence in the uploaded contract to answer this confidently.",
                answer_status="insufficient_evidence",
            )
        citations = [
            SourceCitation(source_id=item["source_id"], chunk_id=str(item["chunk_ordinal"]), page=item["page"], section=item["section"], excerpt=item["text"][:1_000])
            for item in matches
        ]
        question_tokens = self.retrieval._tokens(question)
        expanded_query = self.retrieval._expand_tokens(question_tokens)

        all_candidates: list[tuple[int, str]] = []
        for item in matches:
            paragraphs = [p.strip() for p in re.split(r"\n+", item["text"]) if p.strip()]
            for p in paragraphs:
                if is_heading(p):
                    continue
                splits = [s.strip() for s in SENTENCE_SPLIT_PATTERN.split(p) if s.strip()]
                for s in splits:
                    if not is_heading(s) and len(s) > 20:
                        sentence_tokens = self.retrieval._tokens(s)
                        exact = len(question_tokens & sentence_tokens)
                        expanded = len(expanded_query & sentence_tokens)
                        if exact > 0 or expanded > 0:
                            score = exact * 3 + expanded
                            if "party" in question_tokens and "between" in sentence_tokens:
                                score += 4
                            all_candidates.append((score, s))

        all_candidates.sort(key=lambda item: -item[0])
        answer_sentences: list[str] = []
        for _score, sentence in all_candidates:
            if sentence not in answer_sentences:
                answer_sentences.append(sentence)
                if len(answer_sentences) == 2:
                    break

        if not answer_sentences:
            return ChatAnswer(
                answer="I couldn't find sufficient evidence in the uploaded contract to answer this confidently.",
                answer_status="insufficient_evidence",
                citations=citations,
            )

        return ChatAnswer(
            answer="Based on the contract: " + " ".join(answer_sentences[:2]),
            answer_status="supported",
            citations=citations,
        )
