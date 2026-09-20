from __future__ import annotations

from pathlib import Path

from app.models.repository import ContractRepository
from app.schemas.contracts import ContractAnalysis, ContractStatus
from app.services.analysis_service import AnalysisService
from app.services.document_service import chunk_pages, extract_pdf


class PipelineService:
    def __init__(self, repository: ContractRepository, analysis: AnalysisService) -> None:
        self.repository = repository
        self.analysis = analysis

    def process(self, contract_id: str, filename: str, file_path: Path) -> ContractAnalysis:
        pages = extract_pdf(file_path)
        chunks = chunk_pages(pages, contract_id=contract_id)
        overview, obligations, timeline = self.analysis.analyze(chunks)
        stored_chunks = [
            {"source_id": chunk.source_id, "ordinal": chunk.ordinal, "page": chunk.page, "section": chunk.section, "text": chunk.text}
            for chunk in chunks
        ]
        self.repository.save(contract_id, filename, file_path, len(pages), overview.model_dump(), [item.model_dump() for item in obligations], [item.model_dump() for item in timeline], stored_chunks)
        stored = self.repository.get(contract_id)
        assert stored is not None
        return self._analysis_from_record(contract_id, stored)

    def get_status(self, contract_id: str) -> ContractStatus | None:
        record = self.repository.get(contract_id)
        if not record:
            return None
        return ContractStatus(id=contract_id, filename=record["filename"], page_count=record["page_count"], status=record["status"], uploaded_at=record["uploaded_at"])

    def get_analysis(self, contract_id: str) -> ContractAnalysis | None:
        record = self.repository.get(contract_id)
        return self._analysis_from_record(contract_id, record) if record else None

    @staticmethod
    def _analysis_from_record(contract_id: str, record: dict) -> ContractAnalysis:
        return ContractAnalysis(id=contract_id, filename=record["filename"], page_count=record["page_count"], status=record["status"], uploaded_at=record["uploaded_at"], overview=record["overview"], obligations=record["obligations"], timeline=record["timeline"])
