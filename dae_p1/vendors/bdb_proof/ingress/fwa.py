from __future__ import annotations
from typing import Any, Dict
from .base import IngressAdapter, RawIngest
from ..core.types import Observation

class FWAIngressAdapter(IngressAdapter):
    domain = "fwa"

    def normalize(self, raw: RawIngest) -> Observation:
        p = raw.payload
        metrics = {
            "rsrp": p.get("rsrp"),
            "rsrq": p.get("rsrq"),
            "sinr": p.get("sinr"),
            "wan_rtt_ms": p.get("wan_rtt_ms"),
            "wan_loss_pct": p.get("wan_loss_pct"),
            "cell_id": p.get("cell_id"),
            "band": p.get("band"),
        }
        events = []
        if p.get("re_attach"):
            events.append({"type": "re_attach", "detail": p.get("re_attach")})
        if p.get("cell_change"):
            events.append({"type": "cell_change", "detail": p.get("cell_change")})
        return Observation(ts=raw.ts, domain="fwa", device_id=raw.device_id, metrics=metrics, events=events)
