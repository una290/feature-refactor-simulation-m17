from __future__ import annotations

import datetime as dt
from typing import List, Optional, Tuple

from .types import (
    AdmissionRequest,
    AdmissionVerdict,
    OperativeExecutionState,
    RecognitionResult,
    RecognitionVerdict,
)


def _is_expired(not_after: Optional[dt.datetime], now: dt.datetime) -> bool:
    if not_after is None:
        return False
    return not_after <= now


def _is_stale(issued_ts: dt.datetime, staleness_seconds: Optional[int], now: dt.datetime) -> bool:
    if staleness_seconds is None:
        return False
    return (now - issued_ts).total_seconds() > float(staleness_seconds)


def check_recognizability(req: AdmissionRequest, now: Optional[dt.datetime] = None) -> Tuple[bool, List[str], Optional[str], Optional[str]]:
    """Return (recognizable, reasons, authority_scope_ref, validity_horizon_ref)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    reasons: List[str] = []

    auth = req.recognition.authority_scope
    if auth is None:
        reasons.append("AUTHORITY_SCOPE_ABSENT")
    else:
        if _is_expired(auth.not_after_ts, now):
            reasons.append("AUTHORITY_SCOPE_EXPIRED")

    hz = req.recognition.validity_horizon
    if hz is None:
        reasons.append("VALIDITY_HORIZON_ABSENT")
    else:
        if _is_expired(hz.not_after_ts, now):
            reasons.append("VALIDITY_HORIZON_EXPIRED")
        if _is_stale(hz.issued_ts, hz.staleness_seconds, now):
            reasons.append("VALIDITY_HORIZON_STALE")

    recognizable = len(reasons) == 0
    return recognizable, reasons, (auth.authority_scope_ref if auth else None), (hz.validity_horizon_ref if hz else None)


def map_to_operative_state(v: RecognitionVerdict) -> OperativeExecutionState:
    if v == "PERMIT":
        return "OPERATIVE_PERMITTED"
    if v == "DEGRADE":
        return "OPERATIVE_LIMITED"
    if v in ("FREEZE", "COOLDOWN", "ROLLBACK_REQUIRED"):
        return "NON_OPERATIVE_BRAKED"
    if v == "DENY":
        return "NON_OPERATIVE_DENIED"
    if v == "QUARANTINE":
        return "NON_OPERATIVE_QUARANTINED"
    return "NON_RECOGNIZABLE"


def evaluate_recognition(
    req: AdmissionRequest,
    admission_verdict: AdmissionVerdict,
    extra_reason_codes: Optional[List[str]] = None,
    now: Optional[dt.datetime] = None,
) -> RecognitionResult:
    """Evaluate recognition verdict and operative execution-state semantics."""
    recognizable, reasons, auth_ref, hz_ref = check_recognizability(req, now=now)

    reason_codes: List[str] = []
    if extra_reason_codes:
        reason_codes.extend(extra_reason_codes)
    reason_codes.extend(reasons)

    if not recognizable:
        v: RecognitionVerdict = "NON_RECOGNIZABLE"
        return RecognitionResult(
            recognition_verdict=v,
            operative_state=map_to_operative_state(v),
            reason_codes=sorted(list(dict.fromkeys(reason_codes))),
            authority_scope_ref=auth_ref,
            validity_horizon_ref=hz_ref,
        )

    # Recognizable: recognition verdict follows the admission verdict in this ref impl.
    v2: RecognitionVerdict = admission_verdict  # type: ignore[assignment]
    return RecognitionResult(
        recognition_verdict=v2,
        operative_state=map_to_operative_state(v2),
        reason_codes=sorted(list(dict.fromkeys(reason_codes))),
        authority_scope_ref=auth_ref,
        validity_horizon_ref=hz_ref,
    )
