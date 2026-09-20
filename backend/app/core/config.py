from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    database_path: Path = ROOT_DIR / "data" / "contractlens.db"
    upload_dir: Path = ROOT_DIR / "data" / "uploads"
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    ai_mode: str = os.getenv("AI_MODE", "heuristic")
    llm_model: str = os.getenv("LLM_MODEL", "")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()
    )


settings = Settings()
