from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Optional, List
from .types import EvidenceBundle

SCHEMA = '''
CREATE TABLE IF NOT EXISTS evidence (
  evidence_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  device_id TEXT NOT NULL,
  created_ts TEXT NOT NULL,
  window_id TEXT NOT NULL,
  admission_verdict TEXT NOT NULL,
  payload_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_case_id ON evidence(case_id);
'''

class EvidenceStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self):
        con = sqlite3.connect(self.db_path)
        try:
            con.executescript(SCHEMA)
            con.commit()
        finally:
            con.close()

    def put(self, bundle: EvidenceBundle):
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                "INSERT OR REPLACE INTO evidence(evidence_id, case_id, device_id, created_ts, window_id, admission_verdict, payload_json) VALUES (?,?,?,?,?,?,?)",
                (
                    bundle.evidence_id,
                    bundle.case.case_id,
                    bundle.case.device_id,
                    bundle.created_ts.isoformat(),
                    bundle.window_ref.window_id,
                    bundle.admission_verdict,
                    bundle.model_dump_json(),
                ),
            )
            con.commit()
        finally:
            con.close()

    def get_latest_for_case(self, case_id: str) -> Optional[EvidenceBundle]:
        con = sqlite3.connect(self.db_path)
        try:
            row = con.execute(
                "SELECT payload_json FROM evidence WHERE case_id=? ORDER BY created_ts DESC LIMIT 1",
                (case_id,),
            ).fetchone()
            if not row:
                return None
            from .types import EvidenceBundle
            return EvidenceBundle.model_validate_json(row[0])
        finally:
            con.close()

    def list_case_ids(self, limit: int = 50) -> List[str]:
        con = sqlite3.connect(self.db_path)
        try:
            rows = con.execute(
                "SELECT DISTINCT case_id FROM evidence ORDER BY created_ts DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [r[0] for r in rows]
        finally:
            con.close()
