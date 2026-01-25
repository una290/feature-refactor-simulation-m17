from __future__ import annotations
from typing import Dict, Any, List
from .types import TriageVerdict

def triage_from_summary(summary: Dict[str, Any]) -> TriageVerdict:
    # Heuristic triage intended for closure-routing, not optimization.
    # Open-set: operators may replace with their own mapping/playbook.
    wan_score = 0.0
    wifi_score = 0.0
    dev_score = 0.0
    reasons: List[str] = []

    # WAN indicators
    if summary.get("wan_rtt_ms", 0) > 120: 
        wan_score += 2; reasons.append("WAN_RTT_HIGH")
    if summary.get("wan_loss_pct", 0) > 2:
        wan_score += 2; reasons.append("WAN_LOSS_HIGH")
    if summary.get("event_re_attach", 0) >= 1:
        wan_score += 1; reasons.append("FWA_RE_ATTACH")
    if summary.get("event_cell_change", 0) >= 1:
        wan_score += 1; reasons.append("FWA_CELL_CHANGE")

    # Wi-Fi indicators
    if summary.get("retry_rate", 0) > 0.15:
        wifi_score += 2; reasons.append("WIFI_RETRY_HIGH")
    if summary.get("airtime_busy", 0) and summary["airtime_busy"] > 0.75:
        wifi_score += 2; reasons.append("WIFI_AIRTIME_BUSY")
    if summary.get("steer_count", 0) and summary["steer_count"] > 10:
        wifi_score += 2; reasons.append("WIFI_STEERING_HIGH")
    if summary.get("event_steering", 0) >= 3:
        wifi_score += 1; reasons.append("WIFI_STEERING_EVENTS")

    # Device/Thermal indicators
    if summary.get("temp_c", 0) and summary["temp_c"] > 85:
        dev_score += 2; reasons.append("THERMAL_HOT")
    if summary.get("throttle") is True:
        dev_score += 2; reasons.append("THERMAL_THROTTLE")
    if summary.get("event_reboot", 0) >= 1:
        dev_score += 2; reasons.append("DEVICE_REBOOT")

    scores = {"WAN-dominant": wan_score, "WiFi-dominant": wifi_score, "Device-dominant": dev_score}
    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    if top[0][1] == 0:
        return TriageVerdict(label="Uncertain", confidence="low", reason_codes=reasons, notes="Insufficient signals in this window.")
    # Mixed if close
    if len(top) >= 2 and (top[0][1] - top[1][1]) <= 1.0 and top[1][1] > 0:
        return TriageVerdict(label="Mixed", confidence="low", reason_codes=reasons, notes="Signals indicate multiple contributing domains.")
    conf = "high" if top[0][1] >= 4 else ("med" if top[0][1] >= 2 else "low")
    return TriageVerdict(label=top[0][0], confidence=conf, reason_codes=reasons, notes="Closure-routing triage (non-binding).")
