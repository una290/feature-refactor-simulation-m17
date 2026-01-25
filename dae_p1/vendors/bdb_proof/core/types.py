from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Domain = Literal["fwa", "wifi", "thermal", "unknown"]
TriageLabel = Literal["WAN-dominant", "WiFi-dominant", "Device-dominant", "Mixed", "Uncertain"]

# Admission verdicts are conservative brakes at the gate.
AdmissionVerdict = Literal[
    "PERMIT",
    "DENY",
    "DEGRADE",
    "FREEZE",
    "COOLDOWN",
    "ROLLBACK_REQUIRED",
    "QUARANTINE",
]

# Recognition verdicts add *recognizability* semantics.
# "NON_RECOGNIZABLE" means the attempted act is not admissible for governance/responsibility
# attribution regardless of any observed physical/compute side effects.
RecognitionVerdict = Literal[
    "PERMIT",
    "DENY",
    "DEGRADE",
    "FREEZE",
    "COOLDOWN",
    "ROLLBACK_REQUIRED",
    "QUARANTINE",
    "NON_RECOGNIZABLE",
]

# Operative execution state is a recordable status (not "code executed").
OperativeExecutionState = Literal[
    "OPERATIVE_PERMITTED",
    "OPERATIVE_LIMITED",
    "NON_OPERATIVE_DENIED",
    "NON_OPERATIVE_QUARANTINED",
    "NON_OPERATIVE_BRAKED",
    "NON_RECOGNIZABLE",
]

Readiness = Literal["SUFFICIENT", "INSUFFICIENT"]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


class SnapshotRefs(BaseModel):
    policy_snapshot_ref: str = Field(default_factory=lambda: new_id("policy"))
    version_ref: str = Field(default_factory=lambda: new_id("ver"))
    basis_ref: str = Field(default_factory=lambda: new_id("basis"))


class WindowRef(BaseModel):
    window_id: str
    start_ts: dt.datetime
    end_ts: dt.datetime


class Observation(BaseModel):
    obs_id: str = Field(default_factory=lambda: new_id("obs"))
    ts: dt.datetime
    domain: Domain
    device_id: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)


class CaseContext(BaseModel):
    case_id: str = Field(default_factory=lambda: new_id("case"))
    device_id: str
    customer_id: Optional[str] = None
    site_id: Optional[str] = None


class AttemptMeta(BaseModel):
    # Attempt-always trace fields (minimal open set)
    attempt_id: str = Field(default_factory=lambda: new_id("attempt"))
    origin_ref: str = "unknown_origin"  # e.g., csr_ui, operator_console, automation
    intent_tag: str = "unknown_intent"
    action_pack_id: Optional[str] = None  # referenceable remediation package (open set)


class AuthorityScope(BaseModel):
    # Referenceable authority scope. Schema is open-set.
    authority_scope_ref: str = Field(default_factory=lambda: new_id("scope"))
    issuer_ref: str = "unknown_issuer"
    scope: Dict[str, Any] = Field(default_factory=dict)
    issued_ts: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    not_after_ts: Optional[dt.datetime] = None
    version_ref: str = Field(default_factory=lambda: new_id("scopever"))


class ValidityHorizon(BaseModel):
    # Validity horizon for recognition (can be time-based or policy-based; open set).
    validity_horizon_ref: str = Field(default_factory=lambda: new_id("horizon"))
    issued_ts: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    not_after_ts: Optional[dt.datetime] = None
    staleness_seconds: Optional[int] = None  # if set, horizon is stale after this many seconds


class RecognitionPreconditions(BaseModel):
    # Preconditions that gate recognizability.
    authority_scope: Optional[AuthorityScope] = None
    validity_horizon: Optional[ValidityHorizon] = None
    recognition_boundary_id: str = "REC_BOUNDARY_DEFAULT"


class TriageVerdict(BaseModel):
    label: TriageLabel
    confidence: Literal["high", "med", "low"] = "med"
    reason_codes: List[str] = Field(default_factory=list)
    notes: str = ""


class BoundaryHit(BaseModel):
    boundary_id: str
    severity: Literal["info", "warn", "critical"]
    reason_code: str
    details: Dict[str, Any] = Field(default_factory=dict)


class BoundaryEval(BaseModel):
    hits: List[BoundaryHit] = Field(default_factory=list)

    @property
    def max_severity(self) -> str:
        order = {"info": 0, "warn": 1, "critical": 2}
        best = "info"
        for h in self.hits:
            if order[h.severity] > order[best]:
                best = h.severity
        return best


class AdmissionRequest(BaseModel):
    case: CaseContext

    # Requested act context (open set)
    requested_action_class: str = "unknown_action"

    # Attribution / actor fields (open set)
    actor_ref: str = "unknown_actor"

    # Decision Ticket / constrained authorization reference
    decision_ticket_id: str = Field(default_factory=lambda: new_id("ticket"))

    # Attempt-always trace fields
    attempt: AttemptMeta = Field(default_factory=AttemptMeta)

    # Recognition boundary prerequisites
    recognition: RecognitionPreconditions = Field(default_factory=RecognitionPreconditions)

    # Decision basis snapshots
    snapshot_refs: SnapshotRefs = Field(default_factory=SnapshotRefs)


class CounterforceAction(BaseModel):
    action: AdmissionVerdict
    constraint_delta_ref: str = Field(default_factory=lambda: new_id("delta"))
    cooldown_seconds: Optional[int] = None
    scope: Dict[str, Any] = Field(default_factory=dict)


class ReadinessVerdict(BaseModel):
    readiness: Readiness
    missing_fields: List[str] = Field(default_factory=list)
    notes: str = ""


class FPLiteOutput(BaseModel):
    # FP Lite: compress a window into stable, comparable states (no raw payload required).
    fp_lite_version: str = "fp-lite-v0"
    facet_levels: Dict[str, int] = Field(default_factory=dict)  # open-set facets -> level 0..3
    regime_code: str = "R0"
    notes: str = ""


class RecognitionResult(BaseModel):
    recognition_verdict: RecognitionVerdict
    operative_state: OperativeExecutionState
    reason_codes: List[str] = Field(default_factory=list)
    authority_scope_ref: Optional[str] = None
    validity_horizon_ref: Optional[str] = None


class EvidenceBundle(BaseModel):
    evidence_id: str = Field(default_factory=lambda: new_id("evid"))
    created_ts: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))

    case: CaseContext
    attempt: AttemptMeta

    window_ref: WindowRef

    triage: TriageVerdict
    fp_lite: FPLiteOutput
    boundary_eval: BoundaryEval
    readiness: ReadinessVerdict

    admission_verdict: AdmissionVerdict
    recognition: RecognitionResult

    # Consolidated reason codes (open set)
    reason_codes: List[str] = Field(default_factory=list)

    snapshot_refs: SnapshotRefs

    # Enforcement / trace surface (minimal open set)
    enforcement_path_id: str = Field(default_factory=lambda: new_id("enf"))

    # Counterforce (when any braking happens)
    counterforce: Optional[CounterforceAction] = None
