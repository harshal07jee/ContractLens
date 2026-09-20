from __future__ import annotations

from app.agents.contract_agent import ContractAgent
from app.agents.obligation_agent import ObligationAgent
from app.agents.timeline_agent import TimelineAgent
from app.schemas.contracts import ContractOverview, Obligation, TimelineEvent
from app.services.document_service import DocumentChunk


class AnalysisService:
    """Provider-neutral P0 analysis seam.

    Heuristic mode is intentionally evidence-first and deterministic. A configured LLM provider
    can replace these calls later without changing routes or persistence contracts.
    """

    def __init__(self) -> None:
        self.contract_agent = ContractAgent()
        self.obligation_agent = ObligationAgent()
        self.timeline_agent = TimelineAgent()

    def analyze(self, chunks: list[DocumentChunk]) -> tuple[ContractOverview, list[Obligation], list[TimelineEvent]]:
        return (
            self.contract_agent.analyze(chunks),
            self.obligation_agent.extract(chunks),
            self.timeline_agent.extract(chunks),
        )
