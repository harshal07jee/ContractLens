# ContractLens Architecture

## Scope and principles

This is a two-day, single-deployment MVP. It uses one Next.js frontend and one FastAPI backend; agents are ordinary backend modules, not independently deployed services. The primary invariant is evidence preservation: every extracted fact, timeline item, and answer must retain page, section, chunk, and quoted-text provenance. The product offers informational assistance only and must not make legal determinations.

## System shape

```text
Next.js frontend
  | HTTP
FastAPI backend
  |- upload and processing orchestration
  |- document extraction and page-aware chunking
  |- agent modules and evidence verification
  |- retrieval and AI-provider abstractions
  |- SQLite metadata + local vector index + file storage
```

The frontend owns the product experience: landing page, upload, dashboard, overview, obligations, timeline, chat, and source viewer. The backend owns all document handling, prompts, model calls, validation, persistence, and citation generation. Browser code never receives an AI key or accesses contract storage directly.

## Processing flow

```text
PDF upload
  -> validation and durable file storage
  -> page-aware text extraction
  -> section detection and chunking
  -> chunk persistence and embeddings
  -> Contract Analyzer / Obligation / Timeline agents
  -> Verification agent
  -> SQLite projections for dashboard
  -> cited responses and source viewer
```

For relative deadlines, store the relationship verbatim (for example, `30 days after invoice`) rather than inventing a date. If an output cannot be supported by stored chunks, return an uncertainty result instead of a citation.

## Backend module boundaries

```text
backend/app/
  api/           Route handlers only; validation and response mapping
  agents/        Contract, obligation, timeline, Q&A, verification modules
  services/      Document processing, AI-provider, embeddings, retrieval, orchestration
  models/        ORM persistence models and repository interfaces
  schemas/       Request/response and structured AI-output schemas
  core/          Settings, logging, errors, and shared constants
```

Agent modules depend on schemas and services, never HTTP routes. Services expose provider-neutral interfaces so the hackathon LLM or embedding model can be replaced. Processing orchestration coordinates the agents in-process and persists results only after validation.

## Core records

`Contract` stores identity, file metadata, processing state, parties, key term projections, and timestamps. `DocumentChunk` stores document ID, text, page number, detected section, chunk order, and vector-index identifier. `Evidence` references an immutable chunk and holds the quoted excerpt used by a claim. `Obligation`, `TimelineEvent`, and `ReviewFlag` each link to one or more evidence records. `ChatTurn` stores the user question, answer, answer state, and evidence references.

This separates source material from AI-derived projections, allowing any dashboard item or answer to open a source viewer without reconstructing citation metadata.

## API contract

| Endpoint | Responsibility |
| --- | --- |
| `POST /api/contracts/upload` | Validate and queue/process a PDF upload |
| `GET /api/contracts/{contract_id}` | Contract metadata and processing status |
| `GET /api/contracts/{contract_id}/overview` | Cited structured key terms and review flags |
| `GET /api/contracts/{contract_id}/obligations` | Cited obligations, filters, and status-ready fields |
| `GET /api/contracts/{contract_id}/timeline` | Cited absolute and relative events |
| `POST /api/contracts/{contract_id}/chat` | Grounded Q&A with evidence or uncertainty |
| `GET /api/contracts/{contract_id}/source/{source_id}` | Source excerpt, page, and section for the viewer |
| `POST /api/contracts/{contract_id}/reprocess` | Optional controlled reprocessing |

All fact-bearing responses should use a common evidence shape: `source_id`, `document_id`, `chunk_id`, `page`, `section`, and `excerpt`. Chat responses also expose `answer_status` (`supported` or `insufficient_evidence`).

## Frontend boundaries

```text
frontend/
  app/           Routes, layouts, page-level data composition
  components/    Reusable product UI: upload, cards, timeline, chat, source viewer
  lib/           Typed API client, formatting, view models
  public/        Static assets
```

The frontend should receive only display-ready DTOs from the backend and show a visible informational-not-legal-advice disclaimer. Source links open the stored excerpt and page context; they do not ask the model to recreate evidence.

## Runtime storage

SQLite holds relational records and the authoritative page/section/source metadata for the MVP. The P0 retriever ranks persisted chunks lexically and returns only the retrieved chunks as citations; this retrieval boundary can be upgraded to a local embedding index without changing the Q&A API. Original files and any generated previews live in a local ignored runtime directory. No managed database, authentication, notifications, or separate agent infrastructure is required for P0.

## Guardrails

- Accept PDFs for P0; reject unsupported, oversized, empty, or unreadable files with user-safe errors.
- Never expose provider keys, internal exceptions, or complete contract text in logs.
- Require an evidence check before presenting material claims or citations.
- Use “Human review recommended” for ambiguity, conflicts, automatic renewal, or interpretation-sensitive clauses.
- Keep model and embedding providers behind service interfaces and configure them via environment variables.

## Implementation order

1. Backend application shell, settings, SQLite schema, and upload validation.
2. PDF extraction, page-aware chunks, and local persistence.
3. AI service abstraction and structured contract/obligation/timeline extraction.
4. Verification and retrieval-backed Q&A with source endpoints.
5. Frontend upload-to-dashboard flow, then obligations, timeline, chat, and source viewer.
6. Demo contract, error states, disclaimer, and end-to-end demo rehearsal.
