from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ContractRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        connection = self._connection()
        try:
            connection.execute("""CREATE TABLE IF NOT EXISTS contracts (
                id TEXT PRIMARY KEY, filename TEXT NOT NULL, file_path TEXT NOT NULL,
                page_count INTEGER NOT NULL, status TEXT NOT NULL, uploaded_at TEXT NOT NULL,
                overview_json TEXT NOT NULL, obligations_json TEXT NOT NULL, timeline_json TEXT NOT NULL
            )""")
            connection.execute("""CREATE TABLE IF NOT EXISTS document_chunks (
                source_id TEXT PRIMARY KEY, contract_id TEXT NOT NULL,
                chunk_ordinal INTEGER NOT NULL, page INTEGER NOT NULL, section TEXT,
                text TEXT NOT NULL,
                FOREIGN KEY(contract_id) REFERENCES contracts(id)
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_contract ON document_chunks(contract_id)")
            connection.commit()
        finally:
            connection.close()

    def save(self, contract_id: str, filename: str, file_path: Path, page_count: int, overview: dict[str, Any], obligations: list[dict[str, Any]], timeline: list[dict[str, Any]], chunks: list[dict[str, Any]]) -> None:
        connection = self._connection()
        try:
            connection.execute("""INSERT INTO contracts VALUES (?, ?, ?, ?, 'processed', ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET status='processed', page_count=excluded.page_count,
                overview_json=excluded.overview_json, obligations_json=excluded.obligations_json, timeline_json=excluded.timeline_json""",
                (contract_id, filename, str(file_path), page_count, datetime.now(timezone.utc).isoformat(), json.dumps(overview), json.dumps(obligations), json.dumps(timeline)))
            connection.execute("DELETE FROM document_chunks WHERE contract_id = ?", (contract_id,))
            connection.executemany(
                "INSERT INTO document_chunks (source_id, contract_id, chunk_ordinal, page, section, text) VALUES (?, ?, ?, ?, ?, ?)",
                [(chunk["source_id"], contract_id, chunk["ordinal"], chunk["page"], chunk["section"], chunk["text"]) for chunk in chunks],
            )
            connection.commit()
        finally:
            connection.close()

    def get(self, contract_id: str) -> dict[str, Any] | None:
        connection = self._connection()
        try:
            row = connection.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,)).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        result = dict(row)
        for key in ("overview_json", "obligations_json", "timeline_json"):
            result[key.removesuffix("_json")] = json.loads(result.pop(key))
        return result

    def chunks_for_contract(self, contract_id: str) -> list[dict[str, Any]]:
        connection = self._connection()
        try:
            rows = connection.execute(
                "SELECT source_id, contract_id, chunk_ordinal, page, section, text FROM document_chunks WHERE contract_id = ? ORDER BY chunk_ordinal",
                (contract_id,),
            ).fetchall()
        finally:
            connection.close()
        return [dict(row) for row in rows]

    def get_source(self, contract_id: str, source_id: str) -> dict[str, Any] | None:
        connection = self._connection()
        try:
            row = connection.execute(
                "SELECT source_id, contract_id, chunk_ordinal, page, section, text FROM document_chunks WHERE contract_id = ? AND source_id = ?",
                (contract_id, source_id),
            ).fetchone()
        finally:
            connection.close()
        return dict(row) if row else None
