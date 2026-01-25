from __future__ import annotations
from typing import Any, Dict
from .base import IngressAdapter, RawIngest
from ..core.types import Observation

class WiFiIngressAdapter(IngressAdapter):
    domain = "wifi"

    def normalize(self, raw: RawIngest) -> Observation:
        p = raw.payload
        metrics = {
            "airtime_busy": p.get("airtime_busy"),
            "retry_rate": p.get("retry_rate"),
            "backhaul_rssi": p.get("backhaul_rssi"),
            "steer_count": p.get("steer_count"),
            "roam_count": p.get("roam_count"),
        }
        events = []
        if p.get("steering"):
            events.append({"type": "steering", "detail": p.get("steering")})
        if p.get("disconnect"):
            events.append({"type": "disconnect", "detail": p.get("disconnect")})
        return Observation(ts=raw.ts, domain="wifi", device_id=raw.device_id, metrics=metrics, events=events)
