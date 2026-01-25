from __future__ import annotations
from typing import Dict, Any, List
from .types import ReadinessVerdict

REQUIRED_FIELDS = [
    # Minimal disclosure fields; open set.
    "domain_fwa",
    "domain_wifi",
    "domain_thermal",
]

def readiness_from_summary(summary: Dict[str, Any]) -> ReadinessVerdict:
    missing: List[str] = []
    for f in REQUIRED_FIELDS:
        if summary.get(f, 0) <= 0:
            missing.append(f)
    if missing:
        return ReadinessVerdict(readiness="INSUFFICIENT", missing_fields=missing, notes="Missing minimal cross-domain observability in this window.")
    return ReadinessVerdict(readiness="SUFFICIENT", missing_fields=[], notes="Minimal observability present for this window.")
