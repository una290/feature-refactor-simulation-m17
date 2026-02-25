
"""
DAE P1 - 19 Modules (Free v1)
Focus: Detect + Recognition + Evidence Freeze/Export + Opaque Risk Flag + Pre-change Snapshot refs
No remediation, no network control, no optimization.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Literal, Tuple
from enum import Enum
import time
import json
import hashlib
import os

def now_ts() -> float:
    return time.time()

def iso(ts: Optional[float]=None) -> str:
    if ts is None: ts = now_ts()
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))

def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

Verdict = Literal["WAN_UNSTABLE","WIFI_CONGESTION","MESH_FLAP","DFS_EVENT","OPAQUE_RISK","UNKNOWN"]

# V1.3 Spec Event Types
class EventType:
    # Wi-Fi 7/8
    MLO_LINK_FLAP = "MLO_LINK_FLAP"
    MESH_BACKHAUL_WEAK = "MESH_BACKHAUL_WEAK"
    OBSS_INTERFERENCE_SPIKE = "OBSS_INTERFERENCE_SPIKE"
    ROAM_STORM = "ROAM_STORM"
    # FWA
    RSRP_DROP_EDGE = "RSRP_DROP_EDGE"
    CELL_RESELECT_STORM = "CELL_RESELECT_STORM"
    RTT_SPIKE_TAIL = "RTT_SPIKE_TAIL"
    # Legacy/Common
    SIGNAL_IMPROVED = "signal_improved"
    SIGNAL_IMPROVED = "signal_improved"
    SIGNAL_DEGRADED = "signal_degraded"
    # Cable
    T3_T4_BURST = "T3_T4_BURST"
    US_RTT_TAIL_SPIKE = "US_RTT_TAIL_SPIKE"
    MER_DROP_EDGE = "MER_DROP_EDGE"

# V1.3 Spec Reason Codes
class ReasonCode:
    # Wi-Fi 7/8
    P95_RTT_TOO_HIGH = "P95_RTT_TOO_HIGH"
    P95_LOSS_TOO_HIGH = "P95_LOSS_TOO_HIGH"
    MESH_BACKHAUL_LIMITER = "MESH_BACKHAUL_LIMITER"
    WIFI_SIDE_OSCILLATION = "WIFI_SIDE_OSCILLATION"
    MLO_ASYMMETRIC_LINK = "MLO_ASYMMETRIC_LINK"
    INSUFFICIENT_SAMPLES = "INSUFFICIENT_SAMPLES"
    # FWA
    WEAK_COVERAGE_RSRP_P5 = "WEAK_COVERAGE_RSRP_P5"
    LOW_SINR_P5 = "LOW_SINR_P5"
    CELL_RESELECT_UNSTABLE = "CELL_RESELECT_UNSTABLE"
    TAIL_RTT_TOO_HIGH = "TAIL_RTT_TOO_HIGH"
    PEAK_CONGESTION_SUSPECT = "PEAK_CONGESTION_SUSPECT"
    PEAK_CONGESTION_SUSPECT = "PEAK_CONGESTION_SUSPECT"
    # Cable
    T3T4_RETRY_BURST = "T3T4_RETRY_BURST"
    TAIL_US_RTT_TOO_HIGH = "TAIL_US_RTT_TOO_HIGH"
    TAIL_US_LOSS_TOO_HIGH = "TAIL_US_LOSS_TOO_HIGH"
    PLANT_IMPAIRMENT_SUSPECT = "PLANT_IMPAIRMENT_SUSPECT"
    # Generic
    PASSED_ALL_CHECKS = "PASSED_ALL_CHECKS"


@dataclass
class PrivacyPolicyRef:
    policy_id: str
    version: str = "1.0"
    is_active: bool = True

@dataclass
class PurposeRef:
    purpose_id: str  # e.g., "network_optimization"

@dataclass
class RetentionRef:
    policy_id: str
    days: int = 30

@dataclass
class DisclosureScopeRef:
    scope_id: str    # e.g., "internal_engineering", "isp_support"

@dataclass
class ProofCard:
    """Unified ProofCard (Capability-Based One Spine)"""
    # --- 1. Identity & Context ---
    episode_id: str
    window_ref: str
    
    # --- 2. Verdict State ---
    primary_verdict: str
    
    # --- 3. Governance Basis ---
    missing_evidence_class: List[str] = field(default_factory=list)
    egress_receipt_ref: Optional[str] = None
    
    # --- 4. Context ---
    byuse_context_ref: Optional[str] = None
    data_range_start: Optional[str] = None
    data_range_end: Optional[str] = None
    
    # --- 5. Privacy & Authorization Refs ---
    refs: Dict[str, Any] = field(default_factory=dict)
    
    # --- 6. Frozen Data Payload (Sensitive) ---
    payload: Optional[Dict[str, Any]] = None

    



@dataclass
class VersionRefs:
    fw: str = "unknown"
    driver: str = "unknown"
    agent: str = "dae_p1/0.1.0"

@dataclass
class MetricSample:
    ts: float
    window_ref: str
    latency_p95_ms: Optional[float] = None
    loss_pct: Optional[float] = None
    retry_pct: Optional[float] = None
    airtime_busy_pct: Optional[float] = None
    roam_count: Optional[int] = None
    mesh_flap_count: Optional[int] = None
    wan_sinr_db: Optional[float] = None
    wan_rsrp_dbm: Optional[float] = None
    wan_reattach_count: Optional[int] = None
    jitter_ms: Optional[float] = None
    in_rate: Optional[float] = None
    out_rate: Optional[float] = None
    cpu_load: Optional[float] = None
    mem_load: Optional[float] = None
    signal_strength_pct: Optional[int] = None
    # Extended metrics for Install Verify
    phy_rate_mbps: Optional[int] = None # Transmit Rate
    phy_rx_rate_mbps: Optional[int] = None # Receive Rate
    channel: Optional[int] = None
    bssid: Optional[str] = None
    radio_type: Optional[str] = None
    band: Optional[str] = None
    dns_status: Optional[str] = None # OK / FAIL
    # Cable Metrics
    t3_count: Optional[int] = None
    t4_count: Optional[int] = None
    us_latency_p95_ms: Optional[float] = None
    us_loss_pct: Optional[float] = None
    ofdm_mer_db: Optional[float] = None
    fec_corrected: Optional[int] = None
    fec_uncorrected: Optional[int] = None

@dataclass
class ChangeEventCard:
    event_time: float
    event_type: str
    origin_hint: str = "unknown"
    trigger: str = "unknown"
    target_scope: str = "unknown"
    change_ref: Optional[str] = None
    version_refs: VersionRefs = field(default_factory=VersionRefs)
    window_ref: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.version_refs, dict):
            self.version_refs = VersionRefs(**self.version_refs)

@dataclass
class PreChangeSnapshot:
    snapshot_ref_id: str
    snapshot_scope: str
    capture_time: float
    snapshot_digest: str
    snapshot_type: str = "periodic"
    readable_fields: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ObservabilityResult:
    observability_status: Literal["SUFFICIENT","INSUFFICIENT"]
    opaque_risk: bool
    missing_refs: List[str] = field(default_factory=list)
    origin_hint: str = "unknown"

@dataclass
class EpisodeRecognition:
    episode_id: str
    episode_start: float
    worst_window_ref: str
    primary_verdict: Verdict
    confidence: float
    evidence_refs: List[str]
    observability: ObservabilityResult

def to_json(obj: Any) -> str:
    def default(o):
        if hasattr(o, "__dataclass_fields__"):
            d = asdict(o)
            return d
        raise TypeError()
    return json.dumps(obj, default=default, ensure_ascii=False, indent=2)
