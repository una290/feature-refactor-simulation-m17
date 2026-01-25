from __future__ import annotations
from typing import Dict, Any, List
from .types import BoundaryHit, BoundaryEval

class BoundaryEngine:
    def __init__(self, policy: Dict[str, Any]):
        self.policy = policy

    def evaluate(self, summary: Dict[str, Any]) -> BoundaryEval:
        hits: List[BoundaryHit] = []

        # 1) Oscillation / high-frequency event boundary (example: steering)
        steer_hi = self.policy["boundaries"]["steering_oscillation"]["steer_count_gt"]
        if summary.get("steer_count", 0) and summary["steer_count"] > steer_hi:
            hits.append(BoundaryHit(
                boundary_id="BND_STEER_OSC",
                severity="critical",
                reason_code="BOUNDARY_STEERING_OSCILLATION",
                details={"steer_count": summary.get("steer_count"), "threshold": steer_hi},
            ))

        # 2) Tail collapse proxy: WAN RTT high + loss
        rtt_hi = self.policy["boundaries"]["wan_tail"]["rtt_ms_gt"]
        loss_hi = self.policy["boundaries"]["wan_tail"]["loss_pct_gt"]
        if (summary.get("wan_rtt_ms", 0) > rtt_hi) and (summary.get("wan_loss_pct", 0) > loss_hi):
            hits.append(BoundaryHit(
                boundary_id="BND_WAN_TAIL",
                severity="warn",
                reason_code="BOUNDARY_WAN_TAIL_COLLAPSE",
                details={"wan_rtt_ms": summary.get("wan_rtt_ms"), "wan_loss_pct": summary.get("wan_loss_pct"),
                         "rtt_thr": rtt_hi, "loss_thr": loss_hi},
            ))

        # 3) Thermal safety boundary
        t_hi = self.policy["boundaries"]["thermal"]["temp_c_gt"]
        if summary.get("temp_c", 0) and summary["temp_c"] > t_hi:
            hits.append(BoundaryHit(
                boundary_id="BND_THERMAL",
                severity="critical",
                reason_code="BOUNDARY_THERMAL_OVERHEAT",
                details={"temp_c": summary.get("temp_c"), "threshold": t_hi},
            ))

        # 4) Evidence sufficiency boundary proxy: lack of domain coverage
        # (Open set; demonstrates 'readiness' integration without requiring payload)
        dom_wifi = summary.get("domain_wifi", 0)
        dom_fwa = summary.get("domain_fwa", 0)
        dom_therm = summary.get("domain_thermal", 0)
        min_obs = self.policy["boundaries"]["readiness"]["min_domain_observations"]
        if (dom_wifi < min_obs) and (dom_fwa < min_obs) and (dom_therm < min_obs):
            hits.append(BoundaryHit(
                boundary_id="BND_READINESS_LOW",
                severity="warn",
                reason_code="BOUNDARY_EVIDENCE_INSUFFICIENT",
                details={"domain_wifi": dom_wifi, "domain_fwa": dom_fwa, "domain_thermal": dom_therm, "min_obs": min_obs},
            ))

        return BoundaryEval(hits=hits)
