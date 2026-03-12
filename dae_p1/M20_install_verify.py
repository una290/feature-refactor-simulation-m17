
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import statistics
from .M00_common import MetricSample

@dataclass
class InstallVerificationResult:
    verify_window_sec: int
    sample_count: int
    readiness_verdict: str  # PASS / MARGINAL / FAIL
    closure_readiness: str  # ready / not_ready
    dominant_factor: str    # WAN / WIFI / MESH / OPAQUE / UNKNOWN
    confidence: float       # 0..1
    fp_vector: Dict[str, float]
    
    # NEW: Why did it pass/fail?
    thresholds: Dict[str, Any] = field(default_factory=dict)
    
    # NEW: Key Info (DNS, Channel, Bandwidth)
    system_info: Dict[str, Any] = field(default_factory=dict)
    
    # NEW: Internal Health (C01, C06)
    internal_health: Dict[str, Any] = field(default_factory=dict)

DEFAULT_VERIFY_WINDOW_SEC = 180  # 3 minutes

from .M13_fp_lite import ProfileManager, QuantileCalculator

def _mean(vals: List[float]) -> Optional[float]:
    if not vals:
        return None
    return float(statistics.mean(vals))

def _vec(samples: List[MetricSample]) -> Dict[str, float]:
    def get(field: str) -> Optional[float]:
        # Handle None gracefully
        v = [getattr(s, field) for s in samples if getattr(s, field) is not None]
        return _mean(v)
        
    out: Dict[str, float] = {}
    # Numeric performance metrics
    for f in ["latency_p95_ms","loss_pct","retry_pct","airtime_busy_pct",
              "mesh_flap_count","wan_sinr_db", "signal_strength_pct",
              "us_latency_p95_ms", "us_loss_pct", "ofdm_mer_db", "t3_count", "t4_count"]:
        m = get(f)
        if m is not None:
            out[f] = m
    return out

def verify_install(samples: List[MetricSample],
                   verify_window_sec: int = DEFAULT_VERIFY_WINDOW_SEC,
                   window_refs: Optional[Dict[str, str]] = None,
                   buffer_stats: Optional[Dict[str, int]] = None) -> InstallVerificationResult:
    """
    Installation Verification (fp_recognition):
    - Uses the last verify_window_sec worth of MetricSample items.
    - Outputs PASS/MARGINAL/FAIL without prescribing remediation.
    - INCLUDES: Thresholds, System Info (DNS/Wifi), and Internals (C01/C06).
    """
    
    # Default Internals if not provided
    internals = {
        "buffer_health": buffer_stats or {"count": 0, "capacity": 0},
        "window_refs": window_refs or {"Ws": "unknown", "Wl": "unknown"}
    }

    if not samples:
        return InstallVerificationResult(
            verify_window_sec, 0, "FAIL", "not_ready", "UNKNOWN", 0.0, {},
            thresholds={"note": "No data available"},
            system_info={},
            internal_health=internals
        )

    end_ts = samples[-1].ts
    start_ts = end_ts - verify_window_sec
    window = [s for s in samples if s.ts >= start_ts]
    
    # If buffer is too short, just use what we have (min 6 samples for confident verdict though)
    if len(window) < 6:
        # Fallback to recent samples if window is empty? No, window logic is robust.
        # But if total samples < 6, effectively we have low confidence.
        if len(samples) < 6:
            window = samples # take all
        else:
            window = samples[-6:] # take last 6

    # 1. Performance Vector
    v = _vec(window)

    latency = v.get("latency_p95_ms", 0.0)
    loss = v.get("loss_pct", 0.0)
    retry = v.get("retry_pct", 0.0)
    airtime = v.get("airtime_busy_pct", 0.0)
    flap = v.get("mesh_flap_count", 0.0)
    sinr = v.get("wan_sinr_db", None)
    signal = v.get("signal_strength_pct", 0.0)

    # 2. Extract System Info (from latest sample)
    last = samples[-1]
    
    # Helper for safe access
    def get_last(k, default="N/A"):
        val = getattr(last, k, None)
        return val if val is not None else default

    sys_info = {
        "domain": get_last("domain", "WIFI"),
        "dns_status": get_last("dns_status", "UNKNOWN"),
        "channel": get_last("channel", 0),
        "radio_type": get_last("radio_type", "unknown"),
        "band": get_last("band", "unknown"),
        "phy_rate_mbps": get_last("phy_rate_mbps", 0),
        "phy_rx_rate_mbps": get_last("phy_rx_rate_mbps", 0)
    }

    # 3. Verdict Logic via M13 ProfileManager
    qc = QuantileCalculator()
    vectors = {
        "rtt_ms": [s.latency_p95_ms for s in window if s.latency_p95_ms is not None],
        "loss_pct": [s.loss_pct for s in window if s.loss_pct is not None],
        "retry_pct": [s.retry_pct for s in window if s.retry_pct is not None],
        "airtime_busy_pct": [s.airtime_busy_pct for s in window if s.airtime_busy_pct is not None],
        "mesh_flap_count": [s.mesh_flap_count for s in window if s.mesh_flap_count is not None],
        "wan_sinr_db": [s.wan_sinr_db for s in window if s.wan_sinr_db is not None],
        "signal_strength_pct": [s.signal_strength_pct for s in window if s.signal_strength_pct is not None],
        "phy_rate_mbps": [s.phy_rate_mbps for s in window if s.phy_rate_mbps is not None],
        "us_rtt_ms": [s.us_latency_p95_ms for s in window if s.us_latency_p95_ms is not None],
        "us_loss_pct": [s.us_loss_pct for s in window if s.us_loss_pct is not None],
        "ofdm_mer_db": [s.ofdm_mer_db for s in window if s.ofdm_mer_db is not None],
        "t3_count": [s.t3_count for s in window if s.t3_count is not None],
        "t4_count": [s.t4_count for s in window if s.t4_count is not None],
        "fec_corrected": [s.fec_corrected for s in window if s.fec_corrected is not None],
        "fec_uncorrected": [s.fec_uncorrected for s in window if s.fec_uncorrected is not None]
    }
    
    p50_map = {k: qc.calculate(vals, 50) for k, vals in vectors.items() if vals}
    p95_map = {k: qc.calculate(vals, 95) for k, vals in vectors.items() if vals}
    p5_map  = {k: qc.calculate(vals, 5) for k, vals in vectors.items() if vals}
    
    domain = sys_info.get("domain", "WIFI")
    profile_ref = "CABLE_INSTALL_ACCEPT" if domain == "CABLE" else "WIFI78_INSTALL_ACCEPT"
    profile = ProfileManager.get(profile_ref)
    check_results = profile.check(p50_map, p95_map, p5_map)
    reasons = [r.reason_code for r in check_results if r.status == "FAIL" and r.reason_code]
    
    dominant = "UNKNOWN"
    is_fail = len(reasons) > 0
    
    if sys_info["dns_status"] == "FAIL":
        dominant = "WAN (DNS)"
        is_fail = True
    elif is_fail:
        from .M00_common import DIAGNOSIS_MAP
        # map first reason code to dominant factor
        rc = reasons[0]
        dominant = DIAGNOSIS_MAP.get(rc, rc)

    verdict = "FAIL" if is_fail else "PASS"
    conf = 0.8 if is_fail else 0.85

    # Boost confidence with more data
    if len(window) >= 18:
        conf = min(0.95, conf + 0.1)

    return InstallVerificationResult(
        verify_window_sec=verify_window_sec,
        sample_count=len(window),
        readiness_verdict=verdict,
        closure_readiness="ready" if verdict == "PASS" else "not_ready",
        dominant_factor=dominant,
        confidence=conf,
        fp_vector=v,
        thresholds={"note": f"Evaluated using {profile_ref} profile from M13", "profile_ref": profile_ref},
        system_info=sys_info,
        internal_health=internals
    )
