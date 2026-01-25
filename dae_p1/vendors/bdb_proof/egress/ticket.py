from __future__ import annotations
from typing import Dict, Any
from ..core.types import EvidenceBundle

def to_ticket_fields(bundle: EvidenceBundle) -> Dict[str, Any]:
    # Minimal example for ServiceNow/Jira/custom: open set mapping.
    triage = bundle.triage.label
    verdict = bundle.admission_verdict
    severity = bundle.boundary_eval.max_severity

    next_step = "WAIT_AND_MONITOR"
    if triage == "WAN-dominant":
        next_step = "CHECK_CELL_CONGESTION_OR_REPOSITION"
    elif triage == "WiFi-dominant":
        next_step = "CHECK_HOME_WIFI_INTERFERENCE_OR_LAYOUT"
    elif triage == "Device-dominant":
        next_step = "ESCALATE_VENDOR_OR_SWAP_DEVICE"
    elif triage in ("Mixed", "Uncertain"):
        next_step = "COLLECT_MIN_FIELDS_OR_DISPATCH_IF_REPEAT"

    if verdict in ("FREEZE", "COOLDOWN"):
        next_step = "FREEZE_AUTOMATION_AND_ESCALATE"

    return {
        "case_id": bundle.case.case_id,
        "device_id": bundle.case.device_id,
        "triage": triage,
        "triage_confidence": bundle.triage.confidence,
        "admission_verdict": verdict,
        "recognition_verdict": bundle.recognition.recognition_verdict,
        "operative_state": bundle.recognition.operative_state,
        "fp_regime_code": bundle.fp_lite.regime_code,
        "boundary_severity": severity,
        "reason_codes": bundle.reason_codes,
        "evidence_id": bundle.evidence_id,
        "window_id": bundle.window_ref.window_id,
        "proof_link_hint": f"/cases/{bundle.case.case_id}/proofcard.pdf",
        "recommended_next_step_class": next_step,
    }
