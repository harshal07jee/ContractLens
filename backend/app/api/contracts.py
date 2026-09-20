from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import settings
from app.models.repository import ContractRepository
from app.schemas.contracts import ChatAnswer, ChatQuestion, ContractAnalysis, ContractOverview, ContractStatus, Obligation, SourceChunk, TimelineEvent
from app.services.analysis_service import AnalysisService
from app.services.document_service import DocumentProcessingError
from app.services.pipeline_service import PipelineService
from app.services.qa_service import QAService


router = APIRouter(prefix="/api/contracts", tags=["contracts"])
pipeline = PipelineService(ContractRepository(settings.database_path), AnalysisService())
qa_service = QAService(pipeline.repository)


@router.post("/upload", response_model=ContractAnalysis, status_code=status.HTTP_201_CREATED)
async def upload_contract(file: UploadFile = File(...)) -> ContractAnalysis:
    filename = Path(file.filename or "contract.pdf").name
    if Path(filename).suffix.lower() != ".pdf" or file.content_type not in {"application/pdf", "application/x-pdf", None}:
        raise HTTPException(status_code=415, detail="This file format is not supported. Please upload a PDF.")
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=422, detail="The uploaded file is empty.")
    if len(contents) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"The PDF exceeds the {settings.max_upload_size_mb} MB upload limit.")
    if not contents.startswith(b"%PDF"):
        raise HTTPException(status_code=422, detail="The uploaded file is not a valid PDF.")
    contract_id = str(uuid4())
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    destination = settings.upload_dir / f"{contract_id}.pdf"
    destination.write_bytes(contents)
    try:
        return pipeline.process(contract_id, filename, destination)
    except DocumentProcessingError as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{contract_id}", response_model=ContractStatus)
def get_contract(contract_id: str) -> ContractStatus:
    result = pipeline.get_status(contract_id)
    if not result:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return result


@router.get("/{contract_id}/overview", response_model=ContractOverview)
def get_contract_overview(contract_id: str) -> ContractOverview:
    result = pipeline.get_analysis(contract_id)
    if not result:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return result.overview


@router.get("/{contract_id}/obligations", response_model=list[Obligation])
def get_contract_obligations(contract_id: str) -> list[Obligation]:
    result = pipeline.get_analysis(contract_id)
    if not result:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return result.obligations


@router.get("/{contract_id}/timeline", response_model=list[TimelineEvent])
def get_contract_timeline(contract_id: str) -> list[TimelineEvent]:
    result = pipeline.get_analysis(contract_id)
    if not result:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return result.timeline


@router.post("/{contract_id}/chat", response_model=ChatAnswer)
def chat_with_contract(contract_id: str, request: ChatQuestion) -> ChatAnswer:
    result = qa_service.answer(contract_id, request.question)
    if result is None:
        raise HTTPException(status_code=404, detail="Contract not found.")
    return result


@router.get("/{contract_id}/source/{source_id}", response_model=SourceChunk)
def get_source(contract_id: str, source_id: str) -> SourceChunk:
    result = qa_service.source(contract_id, source_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Source not found for this contract.")
    return result
