from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .types import EvidenceBundle


SCHEMA = '''
CREATE TABLE IF NOT EXISTS rec_events (
  event_id TEXT PRIMARY KEY,
  device_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  created_ts TEXT NOT NULL,
  day_utc TEXT NOT NULL,
  window_id TEXT NOT NULL,
  triage_label TEXT NOT NULL,
  boundary_severity TEXT NOT NULL,
  fp_regime_code TEXT NOT NULL,
  admission_verdict TEXT NOT NULL,
  recognition_verdict TEXT NOT NULL,
  reason_codes_json TEXT NOT NULL,
  boundary_hits_json TEXT NOT NULL,
  snapshot_refs_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rec_device_day ON rec_events(device_id, day_utc);
CREATE INDEX IF NOT EXISTS idx_rec_case ON rec_events(case_id);
'''


class RecognitionJournalStore:
    """Low-volume 7-day (or N-day) journal over recognition/boundary events.

    This store is designed to keep operator trust:
    - No raw payload required
    - Attempt-always journal entries
    - Queryable daily timeline for CSR/manager views
    """

    def __init__(self, db_path: str, *, retention_days: int = 7):
        self.db_path = db_path
        self.retention_days = int(retention_days)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        con = sqlite3.connect(self.db_path)
        try:
            con.executescript(SCHEMA)
            con.commit()
        finally:
            con.close()

    def put(self, bundle: EvidenceBundle) -> None:
        day = bundle.created_ts.strftime('%Y-%m-%d')
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                """INSERT OR REPLACE INTO rec_events(
                    event_id, device_id, case_id, created_ts, day_utc, window_id,
                    triage_label, boundary_severity, fp_regime_code,
                    admission_verdict, recognition_verdict,
                    reason_codes_json, boundary_hits_json, snapshot_refs_json
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    bundle.evidence_id,  # stable per attempt in this reference impl
                    bundle.case.device_id,
                    bundle.case.case_id,
                    bundle.created_ts.isoformat(),
                    day,
                    bundle.window_ref.window_id,
                    bundle.triage.label,
                    bundle.boundary_eval.max_severity,
                    bundle.fp_lite.regime_code,
                    bundle.admission_verdict,
                    bundle.recognition.recognition_verdict,
                    json.dumps(bundle.reason_codes, ensure_ascii=False),
                    json.dumps([h.model_dump() for h in bundle.boundary_eval.hits], ensure_ascii=False),
                    json.dumps(bundle.snapshot_refs.model_dump(), ensure_ascii=False),
                ),
            )
            con.commit()

            # Best-effort retention cleanup (keep DB bounded for CPE/edge).
            # We store day_utc as YYYY-MM-DD, so simple string compare works.
            if self.retention_days > 0:
                con.execute(
                    "DELETE FROM rec_events WHERE day_utc < date('now', ?)",
                    (f'-{int(self.retention_days)} day',),
                )
                con.commit()
        finally:
            con.close()

    def get_latest(self, device_id: str) -> Optional[Dict[str, Any]]:
        con = sqlite3.connect(self.db_path)
        try:
            row = con.execute(
                "SELECT created_ts, window_id, triage_label, boundary_severity, fp_regime_code, admission_verdict, recognition_verdict, reason_codes_json "
                "FROM rec_events WHERE device_id=? ORDER BY created_ts DESC LIMIT 1",
                (device_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "created_ts": row[0],
                "window_id": row[1],
                "triage": row[2],
                "boundary_severity": row[3],
                "fp_regime_code": row[4],
                "admission_verdict": row[5],
                "recognition_verdict": row[6],
                "reason_codes": json.loads(row[7] or "[]"),
            }
        finally:
            con.close()

    def timeline(self, device_id: str, days: int = 7, limit_events: int = 200) -> Dict[str, Any]:
        """Return a 7-day (or N-day) daily timeline plus a bounded event list."""
        con = sqlite3.connect(self.db_path)
        try:
            rows = con.execute(
                "SELECT day_utc, boundary_severity, recognition_verdict, COUNT(*) "
                "FROM rec_events WHERE device_id=? AND day_utc >= date('now', ?) "
                "GROUP BY day_utc, boundary_severity, recognition_verdict "
                "ORDER BY day_utc ASC",
                (device_id, f'-{int(days)} day'),
            ).fetchall()

            by_day: Dict[str, Any] = {}
            for day, sev, rv, cnt in rows:
                d = by_day.setdefault(day, {"counts": {}})
                key = f"{sev}:{rv}"
                d["counts"][key] = int(cnt)

            ev_rows = con.execute(
                "SELECT created_ts, window_id, triage_label, boundary_severity, fp_regime_code, admission_verdict, recognition_verdict, reason_codes_json "
                "FROM rec_events WHERE device_id=? ORDER BY created_ts DESC LIMIT ?",
                (device_id, int(limit_events)),
            ).fetchall()

            events: List[Dict[str, Any]] = []
            for r in ev_rows:
                events.append(
                    {
                        "created_ts": r[0],
                        "window_id": r[1],
                        "triage": r[2],
                        "boundary_severity": r[3],
                        "fp_regime_code": r[4],
                        "admission_verdict": r[5],
                        "recognition_verdict": r[6],
                        "reason_codes": json.loads(r[7] or "[]"),
                    }
                )

            return {"device_id": device_id, "days": int(days), "daily": by_day, "events": events}
        finally:
            con.close()
