from __future__ import annotations
from typing import Dict, Any, List
import datetime as dt
from .types import AdmissionRequest, EvidenceBundle, CounterforceAction
from .types import AdmissionVerdict
from .boundary import BoundaryEngine
from .triage import triage_from_summary
from .readiness import readiness_from_summary
from .fp_lite import compute_fp_lite
from .recognition import evaluate_recognition
from .windowing import WindowManager
from .aggregator import WindowAggregator

class AdmissionGate:
    '''
    Full BDB: define boundaries, bind to execution-time admission, bind to evidencing.
    Conservative braking only. No tuning / optimization.
    '''
    def __init__(self, policy: Dict[str, Any], wm: WindowManager, agg: WindowAggregator, boundary_engine: BoundaryEngine):
        self.policy = policy
        self.wm = wm
        self.agg = agg
        self.boundary = boundary_engine

    def decide(self, req: AdmissionRequest, window_id: str) -> EvidenceBundle:
        obs_list = self.agg.get(req.case.device_id, window_id)
        summary = self.agg.summarize(obs_list)

        triage = triage_from_summary(summary)
        readiness = readiness_from_summary(summary)
        beval = self.boundary.evaluate(summary)
        fp_cfg = self.policy.get("fp_lite", {}) if isinstance(self.policy, dict) else {}
        fp_lite = compute_fp_lite(
            summary,
            triage=triage,
            beval=beval,
            thresholds=fp_cfg.get("thresholds"),
            version=fp_cfg.get("version", "fp-lite-v0"),
        )

        # Admission logic: conservative braking. Open set policy mapping.
        verdict: AdmissionVerdict = "PERMIT"
        counterforce = None
        reason_codes: List[str] = []

        # Rule 1: evidence insufficient -> COOLDOWN (brake) unless operator overrides (not in this ref impl)
        if readiness.readiness == "INSUFFICIENT":
            verdict = "COOLDOWN"
            counterforce = CounterforceAction(
                action="COOLDOWN",
                cooldown_seconds=self.policy["counterforce"]["cooldown_seconds"],
                scope={"reason": "readiness_insufficient"},
            )
            reason_codes.append("READINESS_INSUFFICIENT")

        # Rule 2: critical boundary hit -> FREEZE (strong brake)
        if beval.max_severity == "critical":
            verdict = "FREEZE"
            counterforce = CounterforceAction(
                action="FREEZE",
                cooldown_seconds=self.policy["counterforce"]["cooldown_seconds"],
                scope={"reason": "critical_boundary"},
            )
            reason_codes.append("BOUNDARY_CRITICAL")

        # Rule 3: warn boundary hit -> DEGRADE (soft brake)
        if (beval.max_severity == "warn") and verdict == "PERMIT":
            verdict = "DEGRADE"
            counterforce = CounterforceAction(
                action="DEGRADE",
                cooldown_seconds=self.policy["counterforce"]["cooldown_seconds"],
                scope={"reason": "warn_boundary"},
            )
            reason_codes.append("BOUNDARY_WARN")

        # Add triage reason codes (closure-routing)
        reason_codes.extend(triage.reason_codes)
        # Add boundary reason codes
        reason_codes.extend([h.reason_code for h in beval.hits])

        # Recognition (recognizability) is independent of physical execution.
        # If prerequisites are missing/stale, the attempt is NON_RECOGNIZABLE.
        rec = evaluate_recognition(req, verdict, extra_reason_codes=reason_codes)
        rec_cfg = self.policy.get("recognition", {}) if isinstance(self.policy, dict) else {}
        if rec.recognition_verdict == "NON_RECOGNIZABLE" and rec_cfg.get("quarantine_on_non_recognizable", True):
            # Conservative: quarantine/brake the act attempt.
            verdict = "QUARANTINE"
            counterforce = CounterforceAction(
                action="QUARANTINE",
                cooldown_seconds=self.policy["counterforce"]["cooldown_seconds"],
                scope={"reason": "non_recognizable"},
            )

        # Consolidate reason codes one more time (include recognizability reasons)
        all_reasons = sorted(list(dict.fromkeys(list(reason_codes) + list(rec.reason_codes))))

        # Bind to evidencing (attempt-always): always produce a window ref
        if obs_list:
            wref = self.wm.window_for(obs_list[-1].ts)
        else:
            wref = self.wm.window_for(dt.datetime.now(dt.timezone.utc))

        return EvidenceBundle(
            case=req.case,
            attempt=req.attempt,
            window_ref=wref,
            triage=triage,
            fp_lite=fp_lite,
            boundary_eval=beval,
            readiness=readiness,
            admission_verdict=verdict,
            recognition=rec,
            reason_codes=all_reasons,
            snapshot_refs=req.snapshot_refs,
            counterforce=counterforce,
        )
