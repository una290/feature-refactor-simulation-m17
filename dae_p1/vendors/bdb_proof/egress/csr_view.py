from __future__ import annotations
from typing import Dict, Any
from ..core.types import EvidenceBundle

def to_csr_view(bundle: EvidenceBundle) -> Dict[str, Any]:
    # 5-line closure-first view for CSR / frontline ops.
    # Not a diagnosis engine. Not decision-binding.
    triage = bundle.triage.label
    verdict = bundle.admission_verdict
    recog = bundle.recognition.recognition_verdict

    closeable = "CLOSEABLE"
    one_line = "Evidence present for this window."
    if bundle.readiness.readiness == "INSUFFICIENT":
        closeable = "NOT_CLOSEABLE"
        one_line = "Insufficient observability for a dispute-ready closure; collect missing fields."
    else:
        if triage == "WAN-dominant":
            one_line = "WAN-side variability detected within window (RTT/loss/attach changes)."
        elif triage == "WiFi-dominant":
            one_line = "Home Wi‑Fi instability detected within window (retry/airtime/steering)."
        elif triage == "Device-dominant":
            one_line = "Device/thermal instability detected within window (heat/throttle/reboot)."
        elif triage == "Mixed":
            one_line = "Multiple domains show signals in the same window; treat as mixed case."
        else:
            one_line = "Signals are weak or ambiguous in this window; treat as uncertain."

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

    if recog == "NON_RECOGNIZABLE":
        closeable = "NOT_CLOSEABLE"
        one_line = "Non-recognizable attempt (missing/invalid authority scope or validity horizon)."
        next_step = "COLLECT_AUTHORITY_SCOPE_AND_RETRY"

    return {
        "closure_verdict": closeable,
        "triage": triage,
        "fp_regime_code": bundle.fp_lite.regime_code,
        "recognition_verdict": recog,
        "one_line_reason": one_line,
        "next_step_class": next_step,
        "evidence_ref": {"evidence_id": bundle.evidence_id, "window_id": bundle.window_ref.window_id},
    }
