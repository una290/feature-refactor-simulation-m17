
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple, NamedTuple, Literal
import statistics
import math
import time
import uuid
import json
from dataclasses import asdict, dataclass
from .M00_common import (
    ReasonCode, ProofCard,
    MetricSample, ChangeEventCard, PreChangeSnapshot, iso
)
from .M10_timeline_builder import TimelineBuilder
from .M22_privacy_governance import PrivacyGovernance


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

@dataclass
class CheckResult:
    name: str # e.g. "Latency (P95)"
    threshold: str # e.g. "<= 60ms"
    actual: str # e.g. "45.2ms"
    status: Literal["PASS", "FAIL"]
    reason_code: Optional[str] = None

class ProfileBase:
    REF = "BASE"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        return []

# --- Wi-Fi 7/8 Profiles ---

class Wifi78InstallAccept(ProfileBase):
    REF = "WIFI78_INSTALL_ACCEPT"
    MIN_SAMPLES = 10
    # Outcome: rtt_ms_p95, loss_rate_p95, wifi_retry_p95, phy_rate_p50
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        results = []
        
        # 1. Latency Check
        val = p95.get("rtt_ms", 0)
        status = "FAIL" if val > 60.0 else "PASS"
        rc = ReasonCode.P95_RTT_TOO_HIGH if status == "FAIL" else None
        results.append(CheckResult("Latency (P95)", "<= 60ms", f"{val:.1f}ms", status, rc))

        # 2. Loss Check
        val = p95.get("loss_pct", 0)
        status = "FAIL" if val > 1.0 else "PASS"
        rc = ReasonCode.P95_LOSS_TOO_HIGH if status == "FAIL" else None
        results.append(CheckResult("Packet Loss (P95)", "<= 1.0%", f"{val:.1f}%", status, rc))

        # 3. Retry Check
        val = p95.get("retry_pct", 0)
        status = "FAIL" if val > 10.0 else "PASS"
        rc = ReasonCode.WIFI_SIDE_OSCILLATION if status == "FAIL" else None
        results.append(CheckResult("Wi-Fi Retry (P95)", "<= 10.0%", f"{val:.1f}%", status, rc))

        # 4. Phy Rate Check
        val = p50.get("phy_rate_mbps", 9999)
        status = "FAIL" if val < 100 else "PASS"
        rc = "LOW_PHY_RATE" if status == "FAIL" else None
        results.append(CheckResult("Phy Rate (P50)", ">= 100Mbps", f"{int(val)}Mbps", status, rc))

        return results

class Wifi78MeshBackhaulSplit(ProfileBase):
    REF = "WIFI78_MESH_BACKHAUL_SPLIT"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        results = []
        # Signal Check (p5 is worst case for signal)
        val = p5.get("backhaul_rssi", -30)
        status = "FAIL" if val < -75 else "PASS"
        rc = ReasonCode.MESH_BACKHAUL_LIMITER if status == "FAIL" else None
        results.append(CheckResult("Backhaul RSSI (P5)", ">= -75dBm", f"{int(val)}dBm", status, rc))
        return results

class Wifi78OscillationGuard(ProfileBase):
    REF = "WIFI78_OSCILLATION_GUARD"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        results = []
        val = p95.get("retry_pct", 0)
        status = "FAIL" if val > 15.0 else "PASS"
        rc = ReasonCode.WIFI_SIDE_OSCILLATION if status == "FAIL" else None
        results.append(CheckResult("Retry Rate (P95)", "<= 15.0%", f"{val:.1f}%", status, rc))
        return results

# --- FWA Profiles ---

class FwaInstallAccept(ProfileBase):
    REF = "FWA_INSTALL_ACCEPT"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        results = []
        # RSRP < -110 dBm
        val = p5.get("wan_rsrp_dbm", -50)
        status = "FAIL" if val < -110 else "PASS"
        rc = ReasonCode.WEAK_COVERAGE_RSRP_P5 if status == "FAIL" else None
        results.append(CheckResult("WAN RSRP (P5)", ">= -110dBm", f"{int(val)}dBm", status, rc))

        # SINR < 0 dB
        val = p5.get("wan_sinr_db", 20)
        status = "FAIL" if val < 0 else "PASS"
        rc = ReasonCode.LOW_SINR_P5 if status == "FAIL" else None
        results.append(CheckResult("WAN SINR (P5)", ">= 0dB", f"{val:.1f}dB", status, rc))
        
        return results

class FwaPlacementGuide(ProfileBase):
    REF = "FWA_PLACEMENT_GUIDE"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        results = []
        # Check signal direction
        val = p5.get("wan_rsrp_dbm", -50)
        status = "FAIL" if val < -100 else "PASS"
        rc = ReasonCode.WEAK_COVERAGE_RSRP_P5 if status == "FAIL" else None
        results.append(CheckResult("WAN RSRP (P5)", ">= -100dBm", f"{int(val)}dBm", status, rc))
        return results

class FwaCongestionSuspect(ProfileBase):
    REF = "FWA_CONGESTION_SUSPECT"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        results = []
        val = p95.get("rtt_ms", 0)
        status = "FAIL" if val > 100.0 else "PASS"
        rc = ReasonCode.TAIL_RTT_TOO_HIGH if status == "FAIL" else None
        results.append(CheckResult("Latency (P95)", "<= 100ms", f"{val:.1f}ms", status, rc))
        return results

# --- Cable Profiles ---

class CableInstallAccept(ProfileBase):
    REF = "CABLE_INSTALL_ACCEPT"
    MIN_SAMPLES = 10
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        results = []
        
        val = p95.get("us_rtt_ms", 0)
        status = "FAIL" if val > 80.0 else "PASS"
        rc = ReasonCode.TAIL_US_RTT_TOO_HIGH if status == "FAIL" else None
        results.append(CheckResult("US Latency (P95)", "<= 80ms", f"{val:.1f}ms", status, rc))

        val = p5.get("ofdm_mer_db", 50)
        status = "FAIL" if val < 32.0 else "PASS"
        rc = ReasonCode.PLANT_IMPAIRMENT_SUSPECT if status == "FAIL" else None
        results.append(CheckResult("OFDM MER (P5)", ">= 32.0dB", f"{val:.1f}dB", status, rc))
        
        return results

class CableUpstreamIntermittent(ProfileBase):
    REF = "CABLE_UPSTREAM_INTERMITTENT"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        results = []
        
        val = p95.get("t3_count", 0)
        status = "FAIL" if val > 5 else "PASS"
        rc = ReasonCode.T3T4_RETRY_BURST if status == "FAIL" else None
        results.append(CheckResult("T3 Count (P95)", "<= 5", f"{int(val)}", status, rc))

        val = p95.get("us_rtt_ms", 0)
        status = "FAIL" if val > 150.0 else "PASS"
        rc = ReasonCode.TAIL_US_RTT_TOO_HIGH if status == "FAIL" else None
        results.append(CheckResult("US Latency (P95)", "<= 150ms", f"{val:.1f}ms", status, rc))

        return results

class CablePlantImpairmentSuspect(ProfileBase):
    REF = "CABLE_PLANT_IMPAIRMENT_SUSPECT"
    MIN_SAMPLES = 20
    
    def check(self, p50: Dict[str, float], p95: Dict[str, float], p5: Dict[str, float]) -> List[CheckResult]:
        results = []
        
        val = p5.get("ofdm_mer_db", 50)
        status = "FAIL" if val < 30.0 else "PASS"
        rc = ReasonCode.PLANT_IMPAIRMENT_SUSPECT if status == "FAIL" else None
        results.append(CheckResult("OFDM MER (P5)", ">= 30.0dB", f"{val:.1f}dB", status, rc))
        
        val = p95.get("fec_corrected", 0)
        status = "FAIL" if val > 1000 else "PASS"
        rc = ReasonCode.PLANT_IMPAIRMENT_SUSPECT if status == "FAIL" else None
        results.append(CheckResult("FEC Corr (P95)", "<= 1000", f"{int(val)}", status, rc))

        return results

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
    Generates Unified ProofCards (V1.3 + Privacy Governance).
    """
    
    def __init__(self):
        self.timeline_builder = TimelineBuilder()
        self.governance = PrivacyGovernance(strict_mode=False)

    def generate(self, 
                 metrics: List[Any], # MetricSample objects or dicts
                 events: List[Any],
                 snapshots: List[Any],
                 profile_ref: str = "WIFI78_INSTALL_ACCEPT",
                 window_ref_str: str = "W-LATEST",
                 manifest_ref_str: str = "TBD",
                 authority_scope_ref: Optional[str] = None,
                 byuse_context_ref: Optional[str] = None) -> ProofCard:
        
        from .M00_common import ObservabilityResult, EpisodeRecognition
        
        # Helper to ensure we have list of dicts for stats calc
        window_data = []
        for m in metrics:
            if hasattr(m, '__dict__'): window_data.append(asdict(m))
            elif isinstance(m, dict): window_data.append(m)
            
        # Calculate Data Range
        min_ts = None
        max_ts = None
        if window_data:
            timestamps = [d.get("ts", 0) for d in window_data if d.get("ts")]
            if timestamps:
                min_ts = min(timestamps)
                max_ts = max(timestamps)
                
        min_ts_iso = iso(min_ts) if min_ts else None
        max_ts_iso = iso(max_ts) if max_ts else None
            
        dummy_rec = EpisodeRecognition(
            episode_id=f"ep-{uuid.uuid4().hex[:8]}",
            episode_start=time.time(),
            worst_window_ref=window_ref_str,
            primary_verdict="UNKNOWN",
            confidence=1.0,
            evidence_refs=[],
            observability=ObservabilityResult("SUFFICIENT", False)
        )
        
        # 1. Pipeline: Base Validity Check (Hook 1)
        is_valid, missing_classes, refs = self.governance.check_base_validity(dummy_rec)
        
        # 2. Freeze First (Timeline Build)
        timeline = self.timeline_builder.build(metrics, events, snapshots)
        
        # 3. Generate Engineering Stats
        eng_card = self._generate_engineering_stats(window_data, profile_ref, window_ref_str, manifest_ref_str, events)
        
        primary_verdict = eng_card.get("verdict", "UNKNOWN")
        if not is_valid:
            primary_verdict = "NOT_READY"
        
        # Combine Timeline + Eng Stats into 'Frozen Data Payload'
        payload = {
            "timeline": timeline,
            "engineering_proof": eng_card,
            "events_debug": [asdict(e) for e in events] if events else []
        }
        
        # 4. Construct Single ProofCard
        pc = ProofCard(
            episode_id=dummy_rec.episode_id,
            window_ref=window_ref_str,
            primary_verdict=primary_verdict,
            missing_evidence_class=missing_classes,
            egress_receipt_ref=None,
            byuse_context_ref=byuse_context_ref,
            data_range_start=min_ts_iso,
            data_range_end=max_ts_iso,
            refs=refs,
            payload=payload
        )
        
        return pc

    def _generate_engineering_stats(self, window_data, profile_ref, window_ref_str, manifest_ref_str, events) -> Dict[str, Any]:
        """Legacy V1.3 Generation Logic (Internal)"""
        # Reuse existing logic to calculate p50/p95
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

        vectors = {
            "rtt_ms": extract("latency_p95_ms") or extract("latency_ms"),
            "loss_pct": extract("loss_pct") or extract("loss_percent"),
            "us_rtt_ms": extract("us_latency_p95_ms"),
            "us_loss_pct": extract("us_loss_pct"),
            "t3_count": extract("t3_count"),
            "t4_count": extract("t4_count"),
            "ofdm_mer_db": extract("ofdm_mer_db"),
            "fec_corrected": extract("fec_corrected"),
            "throughput_mbps": extract("in_rate") or extract("throughput"),
            "retry_pct": extract("retry_pct"),
            "phy_rate_mbps": extract("phy_rate_mbps"),
            "wan_rsrp_dbm": extract("wan_rsrp_dbm"),
            "wan_sinr_db": extract("wan_sinr_db"),
            "backhaul_rssi": extract("signal_strength_pct")
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
        check_results = profile.check(p50_map, p95_map, p5_map)
        
        # Extract reasons from failed checks
        reasons = [r.reason_code for r in check_results if r.status == "FAIL" and r.reason_code]
        
        verdict = "NOT_READY" if reasons else "READY"
        if not reasons: reasons = [ReasonCode.PASSED_ALL_CHECKS]

        # 5. Build Facets
        def to_kv(pmap, suffix):
            return [{"name": f"{k}_{suffix}", "value": v, "unit": "auto"} for k, v in pmap.items()]

        p50_out = to_kv(p50_map, "p50")
        p95_out = to_kv(p95_map, "p95")
        outcome_out = p95_out if verdict != "READY" else p50_out
        if not outcome_out: outcome_out = [{"name": "no_metric_data", "value": 0, "unit": "none"}]

        # 5.1 Extract Event Types
        event_types = []
        if events:
            extracted = set()
            for e in events:
                # Handle objects or dicts
                etype = getattr(e, 'event_type', e.get('event_type') if isinstance(e, dict) else None)
                if etype: extracted.add(etype)
            event_types = list(extracted)
            event_types.sort()

        return self._build_card(
            card_id, profile_ref, verdict, window_ref_str, reasons, n,
            p50_out, p95_out, outcome_out, manifest_ref_str, "VALID",
            event_types, check_results
        )
        
    def _build_card(self, cid, pref, verdict, wref, reasons, n, p50, p95, outcome, mref, validity="VALID", event_types=None, check_results=None):
        if event_types is None: event_types = []
        if check_results is None: check_results = []
        
        return {
            "proof_card_ref": cid,
            "profile_ref": pref,
            "verdict": verdict,
            "window_ref": wref,
            "reason_code": reasons,
            "health_checks": [asdict(r) for r in check_results], # New Field
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
    # Assume bundle payload/timeline has metrics. Detailed reconstruction omitted for brevity in Phase 1-3.
    return {"status": "Mock reconstruction not implemented in this phase"}

