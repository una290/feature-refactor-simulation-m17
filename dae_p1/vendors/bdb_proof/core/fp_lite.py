from __future__ import annotations

from typing import Any, Dict, Optional, List

from .types import BoundaryEval, FPLiteOutput, TriageVerdict


def _lvl(value: Optional[float], thresholds: List[float]) -> int:
    """Map numeric value to a level 0..3 using ascending thresholds."""
    if value is None:
        return 0
    lvl = 0
    for t in thresholds:
        if value > t:
            lvl += 1
    return min(lvl, 3)


def _as_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except Exception:
        return None


def compute_fp_lite(
    summary: Dict[str, Any],
    triage: Optional[TriageVerdict] = None,
    beval: Optional[BoundaryEval] = None,
    *,
    thresholds: Optional[Dict[str, List[float]]] = None,
    version: str = "fp-lite-v0",
) -> FPLiteOutput:
    """Compute FP Lite output from a window summary.

    The mapping is conservative and metadata-friendly. It is intended to provide
    enough capability to earn operator trust while keeping storage minimal.
    """

    thresholds = thresholds or {
        "wan_rtt_ms": [80, 150, 250],
        "wan_loss_pct": [1, 2, 5],
        "retry_rate": [0.05, 0.15, 0.25],
        "airtime_busy": [0.60, 0.75, 0.90],
        "steer_count": [5, 12, 20],
        "temp_c": [70, 85, 92],
    }

    # WAN tail / availability proxy
    wan = max(
        _lvl(_as_float(summary.get("wan_rtt_ms")), thresholds.get("wan_rtt_ms", [80, 150, 250])),
        _lvl(_as_float(summary.get("wan_loss_pct")), thresholds.get("wan_loss_pct", [1, 2, 5])),
    )

    # Wi-Fi instability / oscillation proxy
    wifi = max(
        _lvl(_as_float(summary.get("retry_rate")), thresholds.get("retry_rate", [0.05, 0.15, 0.25])),
        _lvl(_as_float(summary.get("airtime_busy")), thresholds.get("airtime_busy", [0.60, 0.75, 0.90])),
        _lvl(_as_float(summary.get("steer_count")), thresholds.get("steer_count", [5, 12, 20])),
    )

    # Device/thermal instability proxy
    therm = max(
        _lvl(_as_float(summary.get("temp_c")), thresholds.get("temp_c", [70, 85, 92])),
        _lvl(1.0 if summary.get("throttle") is True else 0.0, [0.5, 0.9, 1.1]),
        _lvl(_as_float(summary.get("event_reboot")), [0.5, 1.5, 2.5]),
    )

    # Evidence coverage (minimal cross-domain visibility)
    dom_wifi = _as_float(summary.get("domain_wifi")) or 0.0
    dom_fwa = _as_float(summary.get("domain_fwa")) or 0.0
    dom_th = _as_float(summary.get("domain_thermal")) or 0.0
    missing = sum(1 for x in (dom_wifi, dom_fwa, dom_th) if x <= 0.0)
    if missing == 3:
        coverage = 3
    elif missing == 2:
        coverage = 2
    elif missing == 1:
        coverage = 1
    else:
        coverage = 0

    # Oscillation facet from boundary hits (if present)
    osc = 0
    if beval is not None:
        for h in beval.hits:
            if h.boundary_id == "BND_STEER_OSC":
                if h.severity == "critical":
                    osc = 3
                else:
                    osc = max(osc, 2)

    facets = {
        "WAN_TAIL": int(wan),
        "WIFI_INSTABILITY": int(wifi),
        "DEVICE_THERMAL": int(therm),
        "EVIDENCE_COVERAGE": int(coverage),
        "OSCILLATION": int(osc),
    }

    # Stable, human-readable regime signature.
    # (Open set; callers should treat this as an opaque code for grouping/comparison.)
    regime_code = f"R{wan}{wifi}{therm}{coverage}{osc}"

    # Notes: show the top drivers for operator trust.
    drivers = sorted(facets.items(), key=lambda kv: kv[1], reverse=True)
    top = [f"{k}={v}" for k, v in drivers if v > 0][:3]
    notes = "OK" if not top else "Drivers: " + ", ".join(top)
    if triage is not None:
        notes += f"; triage={triage.label}"

    return FPLiteOutput(
        fp_lite_version=version,
        facet_levels=facets,
        regime_code=regime_code,
        notes=notes,
    )
