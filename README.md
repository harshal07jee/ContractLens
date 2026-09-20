# ContractLens

ContractLens is an AI contract-intelligence MVP that turns uploaded contracts into cited, actionable information: key terms, obligations, dates, human-review flags, and grounded answers.

## Current backend capability

The first P0 backend slice is available: upload a text-readable PDF to extract page-aware contract text, structured contract terms, obligations, timeline events, and retrieval-grounded Q&A. All extracted items and Q&A citations include a source ID, page, detected section when available, and excerpt. It defaults to deterministic `AI_MODE=heuristic`; the analysis service is intentionally isolated so a configured LLM provider can replace it later.

See [the architecture guide](docs/architecture.md) for system boundaries, data flow, API contract, and the recommended implementation order.

## Planned workspace layout

```text
frontend/     Next.js product interface
backend/      FastAPI API, processing pipeline, agents, persistence adapters
docs/         Architecture and delivery documentation
sample_contracts/  Demo-only source documents
data/         Local runtime data (gitignored)
```

## Configuration

Copy `.env.example` to `.env` when implementation begins. Never commit credentials or uploaded contracts.

## Run the backend

From the repository root on Windows:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m uvicorn app.main:app --app-dir backend --reload
```

Open `http://127.0.0.1:8000/docs` to upload a PDF through `POST /api/contracts/upload`. The response contains the structured overview, obligations, timeline, and their evidence. `GET /api/contracts/{contract_id}/overview`, `/obligations`, and `/timeline` return each projection individually. Send `{ "question": "When does this contract expire?" }` to `POST /api/contracts/{contract_id}/chat`; open any returned citation with `GET /api/contracts/{contract_id}/source/{source_id}`.

## Run the dashboard

In a second terminal, set `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000` (or copy the root `.env.example` values into `frontend/.env.local`), then run:

```powershell
cd frontend
pnpm install
pnpm dev
```

Open `http://127.0.0.1:3000`. The dashboard uploads a contract to the backend, presents the extracted overview, obligations and timeline, sends contract questions to the RAG endpoint, and opens citations in a source-evidence drawer.
