
from __future__ import annotations
from typing import List, Dict, Any
from .M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot, iso

class TimelineBuilder:
    """
    Builds a flattened timeline for the last 60 minutes.
    """
    def build(self,
              metrics: List[MetricSample],
              events: List[ChangeEventCard],
              snapshots: List[PreChangeSnapshot]) -> Dict[str, Any]:
        def get_attr(obj, key, default=None):
            return getattr(obj, key, obj.get(key, default) if isinstance(obj, dict) else default)

        return {
            "metrics_points": [
                {
                    "t": iso(get_attr(m, "ts")),
                    "window_ref": get_attr(m, "window_ref"),
                    "latency_p95_ms": get_attr(m, "latency_p95_ms"),
                    "loss_pct": get_attr(m, "loss_pct"),
                    "retry_pct": get_attr(m, "retry_pct"),
                    "airtime_busy_pct": get_attr(m, "airtime_busy_pct"),
                    "mesh_flap_count": get_attr(m, "mesh_flap_count"),
                    "wan_sinr_db": get_attr(m, "wan_sinr_db")
                } for m in metrics
            ],
            "change_events": [
                {
                    "t": iso(get_attr(e, "event_time")),
                    "event_type": get_attr(e, "event_type"),
                    "origin_hint": get_attr(e, "origin_hint"),
                    "target_scope": get_attr(e, "target_scope"),
                    "change_ref": get_attr(e, "change_ref"),
                    "window_ref": get_attr(e, "window_ref")
                } for e in events
            ],
            "pre_change_snapshots": [
                {
                    "t": iso(get_attr(s, "capture_time")),
                    "snapshot_ref_id": get_attr(s, "snapshot_ref_id"),
                    "snapshot_scope": get_attr(s, "snapshot_scope"),
                    "snapshot_digest": get_attr(s, "snapshot_digest"),
                    "snapshot_type": get_attr(s, "snapshot_type"),
                    "readable_fields": get_attr(s, "readable_fields")
                } for s in snapshots
            ]
        }
