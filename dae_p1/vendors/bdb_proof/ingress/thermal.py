from __future__ import annotations
from .base import IngressAdapter, RawIngest
from ..core.types import Observation

class ThermalIngressAdapter(IngressAdapter):
    domain = "thermal"

    def normalize(self, raw: RawIngest) -> Observation:
        p = raw.payload
        metrics = {
            "temp_c": p.get("temp_c"),
            "throttle": p.get("throttle"),
            "cpu_freq_mhz": p.get("cpu_freq_mhz"),
            "uptime_s": p.get("uptime_s"),
            "reboot_reason": p.get("reboot_reason"),
        }
        events = []
        if p.get("throttle_event"):
            events.append({"type": "throttle_event", "detail": p.get("throttle_event")})
        if p.get("reboot"):
            events.append({"type": "reboot", "detail": p.get("reboot")})
        return Observation(ts=raw.ts, domain="thermal", device_id=raw.device_id, metrics=metrics, events=events)
