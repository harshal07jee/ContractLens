from __future__ import annotations

from app.agents.qa_agent import QAAgent
from app.models.repository import ContractRepository
from app.schemas.contracts import ChatAnswer, SourceChunk
from app.services.retrieval_service import RetrievalService


class QAService:
    def __init__(self, repository: ContractRepository) -> None:
        self.repository = repository
        self.agent = QAAgent(RetrievalService())

    def answer(self, contract_id: str, question: str) -> ChatAnswer | None:
        if not self.repository.get(contract_id):
            return None
        return self.agent.answer(question, self.repository.chunks_for_contract(contract_id))

    def source(self, contract_id: str, source_id: str) -> SourceChunk | None:
        source = self.repository.get_source(contract_id, source_id)
        if not source:
            return None
        return SourceChunk(
            source_id=source["source_id"], chunk_id=str(source["chunk_ordinal"]), contract_id=source["contract_id"],
            page=source["page"], section=source["section"], excerpt=source["text"][:1_000], text=source["text"],
        )
