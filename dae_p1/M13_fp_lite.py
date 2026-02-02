
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
import statistics
import math
import time
import uuid
import json
from .M00_common import ReasonCode


# --- 1. Quantile Calculator (Nearest-Rank) ---
class QuantileCalculator:
    @staticmethod
    def calculate(data: List[float], percentile: int) -> float:
        """
        Calculates the p-th percentile using the Nearest-Rank method.
        Definition:
          1) Sort data (ascending).
          2) rank = ceil(p / 100 * N)
          3) result = sorted_data[rank - 1] (0-indexed)
        """
        if not data:
            return 0.0
        
        n = len(data)
        sorted_data = sorted(data)
        rank = math.ceil((percentile / 100.0) * n)
        # minimal rank is 1, max is n
        rank = max(1, min(n, rank))
        return sorted_data[rank - 1]

# --- 2. Data Structures ---
class OutcomeFacet(NamedTuple):
    name: str
    value: Any
    unit: str

class ProofCardResult:
    def __init__(self, card_data: Dict[str, Any]):
        self.card_data = card_data

    def to_dict(self) -> Dict[str, Any]:
        return self.card_data

# --- 3. Profile Definitions ---
# Each profile defines:
# - min_sample_count
# - strict_checks: function(p50_map, p95_map) -> list of failure_reason_codes

class ProfileBase:
    REF = "BASE"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        return []

# --- Wi-Fi 7/8 Profiles ---

class Wifi78InstallAccept(ProfileBase):
    REF = "WIFI78_INSTALL_ACCEPT"
    MIN_SAMPLES = 10
    # Outcome: rtt_ms_p95, loss_rate_p95, wifi_retry_p95, phy_rate_p50
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        # P95 RTT > 60ms (Warning/Fail)
        if p95.get("rtt_ms", 0) > 60.0:
            reasons.append(ReasonCode.P95_RTT_TOO_HIGH)
        # P95 Loss > 1%
        if p95.get("loss_pct", 0) > 1.0:
            reasons.append(ReasonCode.P95_LOSS_TOO_HIGH)
        # Retry > 10%
        if p95.get("retry_pct", 0) > 10.0:
             reasons.append(ReasonCode.WIFI_SIDE_OSCILLATION)
        # Phy Rate < 100Mbps
        if p50.get("phy_rate_mbps", 9999) < 100:
             reasons.append("LOW_PHY_RATE")
        return reasons

class Wifi78MeshBackhaulSplit(ProfileBase):
    REF = "WIFI78_MESH_BACKHAUL_SPLIT"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        # Signal Check (p5 is worst case for signal)
        if p5.get("backhaul_rssi", -30) < -75:
            reasons.append(ReasonCode.MESH_BACKHAUL_LIMITER)
        return reasons

class Wifi78OscillationGuard(ProfileBase):
    REF = "WIFI78_OSCILLATION_GUARD"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p95.get("retry_pct", 0) > 15.0:
             reasons.append(ReasonCode.WIFI_SIDE_OSCILLATION)
        return reasons

# --- FWA Profiles ---

class FwaInstallAccept(ProfileBase):
    REF = "FWA_INSTALL_ACCEPT"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        # RSRP < -110 dBm
        if p5.get("wan_rsrp_dbm", -50) < -110:
             reasons.append(ReasonCode.WEAK_COVERAGE_RSRP_P5)
        # SINR < 0 dB
        if p5.get("wan_sinr_db", 20) < 0:
             reasons.append(ReasonCode.LOW_SINR_P5)
        return reasons

class FwaPlacementGuide(ProfileBase):
    REF = "FWA_PLACEMENT_GUIDE"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        # Check signal direction
        if p5.get("wan_rsrp_dbm", -50) < -100:
             reasons.append(ReasonCode.WEAK_COVERAGE_RSRP_P5)
        return reasons

class FwaCongestionSuspect(ProfileBase):
    REF = "FWA_CONGESTION_SUSPECT"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p95.get("rtt_ms", 0) > 100.0:
            reasons.append(ReasonCode.TAIL_RTT_TOO_HIGH)
        return reasons

# --- Cable Profiles ---

class CableInstallAccept(ProfileBase):
    REF = "CABLE_INSTALL_ACCEPT"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p95.get("us_rtt_ms", 0) > 80.0: # Example
             reasons.append(ReasonCode.TAIL_US_RTT_TOO_HIGH)
        if p5.get("ofdm_mer_db", 50) < 32.0:
             reasons.append(ReasonCode.PLANT_IMPAIRMENT_SUSPECT)
        return reasons

class CableUpstreamIntermittent(ProfileBase):
    REF = "CABLE_UPSTREAM_INTERMITTENT"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p95.get("t3_count", 0) > 5:
             reasons.append(ReasonCode.T3T4_RETRY_BURST)
        if p95.get("us_rtt_ms", 0) > 150.0:
             reasons.append(ReasonCode.TAIL_US_RTT_TOO_HIGH)
        return reasons

class CablePlantImpairmentSuspect(ProfileBase):
    REF = "CABLE_PLANT_IMPAIRMENT_SUSPECT"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[str]:
        reasons = []
        if p5.get("ofdm_mer_db", 50) < 30.0:
             reasons.append(ReasonCode.PLANT_IMPAIRMENT_SUSPECT)
        if p95.get("fec_corrected", 0) > 1000:
             reasons.append(ReasonCode.PLANT_IMPAIRMENT_SUSPECT)
        return reasons

class ProfileManager:
    PROFILES = {
        Wifi78InstallAccept.REF: Wifi78InstallAccept(),
        Wifi78MeshBackhaulSplit.REF: Wifi78MeshBackhaulSplit(),
        Wifi78OscillationGuard.REF: Wifi78OscillationGuard(),
        FwaInstallAccept.REF: FwaInstallAccept(),
        FwaPlacementGuide.REF: FwaPlacementGuide(),
        FwaCongestionSuspect.REF: FwaCongestionSuspect(),
        CableInstallAccept.REF: CableInstallAccept(),
        CableUpstreamIntermittent.REF: CableUpstreamIntermittent(),
        CablePlantImpairmentSuspect.REF: CablePlantImpairmentSuspect()
    }
    
    @staticmethod
    def get(ref: str) -> ProfileBase:
        return ProfileManager.PROFILES.get(ref, ProfileBase())

# --- 4. Main Generator ---

class ProofCardGenerator:
    """
    Generates V1.3 ProofCards from raw window data.
    """
    
    def __init__(self):
        pass

    def generate(self, 
                 window_data: List[Dict[str, Any]], 
                 profile_ref: str, 
                 window_ref_str: str,
                 manifest_ref_str: str = "TBD",
                 events: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        
        # 0. Prep
        card_id = f"pc-{uuid.uuid4().hex[:12]}"
        ts_now = time.time()
        profile = ProfileManager.get(profile_ref)
        
        # 1. Sample Count Check
        n = len(window_data)
        if n < profile.MIN_SAMPLES:
            return self._build_card(card_id, profile_ref, "INSUFFICIENT_EVIDENCE", 
                                    window_ref_str, ["INSUFFICIENT_SAMPLES"], 
                                    n, [], [], 
                                    [{"name": "sample_count", "value": n, "unit": "count"}], 
                                    manifest_ref_str)

        # 2. Key Metrics Extraction
        # We need to map raw data keys to 'rtt_ms', 'loss_pct' etc.
        # Assuming window_data comes from core.metrics_buf (MetricSample items)
        
        def extract(key):
            vals = []
            for d in window_data:
                val = d.get(key)
                if val is not None:
                     try:
                         vals.append(float(val))
                     except (TypeError, ValueError):
                         pass
            return vals

        # Map: metric_name -> list of values
        # This mapping depends on what module generates (M03 MetricsCollector)
        # For now, we perform a loose mapping
        vectors = {
            # Updated to match M00 MetricSample fields
            "rtt_ms": extract("latency_p95_ms") or extract("latency_ms"),
            "loss_pct": extract("loss_pct") or extract("loss_percent"),
            # Cable Mapping
            "us_rtt_ms": extract("us_latency_p95_ms"),
            "us_loss_pct": extract("us_loss_pct"),
            "t3_count": extract("t3_count"),
            "t4_count": extract("t4_count"),
            "ofdm_mer_db": extract("ofdm_mer_db"),
            "fec_corrected": extract("fec_corrected"),
            
            "throughput_mbps": extract("in_rate") or extract("throughput"),
            # New V1.3 Fields
            "retry_pct": extract("retry_pct"),
            "phy_rate_mbps": extract("phy_rate_mbps"),
            "wan_rsrp_dbm": extract("wan_rsrp_dbm"),
            "wan_sinr_db": extract("wan_sinr_db"),
            "backhaul_rssi": extract("signal_strength_pct") # Using sig% as proxy for demo
        }
        
        # 3. Compute p50 / p95 / p5
        p50_map = {}
        p95_map = {}
        p5_map  = {}
        
        qc = QuantileCalculator()
        
        for k, vals in vectors.items():
            if vals:
                p50_map[k] = qc.calculate(vals, 50)
                p95_map[k] = qc.calculate(vals, 95)
                p5_map[k]  = qc.calculate(vals, 5)

        # 4. Assess Verdict
        reasons = profile.check(p50_map, p95_map, p5_map)
        if reasons:
            verdict = "NOT_READY"
        else:
            verdict = "READY"
            reasons = [ReasonCode.PASSED_ALL_CHECKS]


        # 5. Build Facets
        # Construct output arrays
        def to_kv(pmap, suffix):
            return [{"name": f"{k}_{suffix}", "value": v, "unit": "auto"} for k, v in pmap.items()]

        p50_out = to_kv(p50_map, "p50")
        p95_out = to_kv(p95_map, "p95")
        
        # Core outcome facets - usually a mix of p50/p95 relevant to the profile
        # For simplicity, we dump all p95s as outcome facets if invalid, or p50 if valid
        outcome_out = p95_out if verdict != "READY" else p50_out
        if not outcome_out: 
             outcome_out = [{"name": "no_metric_data", "value": 0, "unit": "none"}]

        # 5.1 Extract Event Types
        event_types = []
        if events:
            # Extract 'event_type' from each event dict
            extracted = set()
            for e in events:
                etype = e.get("event_type")
                if etype:
                    extracted.add(etype)
            event_types = list(extracted)
            event_types.sort() # Ensure deterministic order

        # 6. Assess Validity (V1.3 Spec)
        # Check freshness of data
        ts_newest = 0
        ts_oldest = float('inf')
        
        for d in window_data:
            t = d.get('ts', 0)
            if t > ts_newest: ts_newest = t
            if t < ts_oldest: ts_oldest = t
            
        validity_verdict = "VALID"
        age_sec = ts_now - ts_newest
        
        # Rule: If data is older than 24h, mark STALE (but valid for historical query)
        if age_sec > 86400:
            validity_verdict = "STALE"
            
        # Rule: If data is outside 7 days retention, theoretically it shouldn't be here, 
        # but if we see it, it is OUT_OF_SCOPE.
        if (ts_now - ts_oldest) > (7 * 86400):
             validity_verdict = "OUT_OF_SCOPE"

        return self._build_card(
            card_id, profile_ref, verdict, window_ref_str, reasons, n,
            p50_out, p95_out, outcome_out, manifest_ref_str, validity_verdict,
            event_types
        )

    def _build_card(self, cid, pref, verdict, wref, reasons, n, p50, p95, outcome, mref, validity="VALID", event_types=None):
        if event_types is None:
            event_types = []
        return {
            "proof_card_ref": cid,
            "profile_ref": pref,
            "verdict": verdict,
            "window_ref": wref,
            "reason_code": reasons,
            "enforcement_path_ref": "EP-DEFAULT-01",
            "authority_scope_ref": "SCOPE-CPE-LOCAL",
            "validity_horizon_ref": "7DAYS",
            "validity_verdict": validity,
            "basis_ref": "BASIS-V1.3",
            "sample_count": n,
            "p50": p50,
            "p95": p95,
            "outcome_facet": outcome,
            "event_type": event_types,
            "evidence_bundle_ref": f"bundle:{wref}",
            "manifest_ref": mref
        }


def fp_lite_from_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to generate ProofCard from a bundle dict (for offline/test use).
    """
    gen = ProofCardGenerator()
    return gen.generate(
        window_data=bundle.get("window_data", []),
        profile_ref=bundle.get("profile_ref", "BASE"),
        window_ref_str=bundle.get("window_ref", "unknown"),
        manifest_ref_str=bundle.get("manifest_ref", "TBD"),
        events=bundle.get("events", [])
    )
