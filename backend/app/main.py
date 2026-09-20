from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.contracts import router as contracts_router
from app.core.config import settings


app = FastAPI(title="ContractLens API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(contracts_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
