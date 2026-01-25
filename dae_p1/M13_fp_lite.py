
from __future__ import annotations
from typing import Dict, Any, List
from .M00_common import MetricSample
from .vendors.bdb_proof.core.fp_lite import compute_fp_lite
from .vendors.bdb_proof.core.aggregator import WindowAggregator
from .vendors.bdb_proof.core.windowing import WindowManager

from .vendors.bdb_proof.core.types import Observation

def compute_fingerprint_lite(metrics: List[MetricSample]) -> Dict[str, Any]:
    """
    Computes a 'Lite' fingerprint using the V2 Core Logic.
    
    This function adapts old 'MetricSample' inputs into V2 'Observation' objects,
    feeds them into a V2 'WindowAggregator', and then calls the V2 'compute_fp_lite'.
    """
    # 1. Adapt Metrics -> Observations
    obs_list = []
    for m in metrics:
        # Simplistic mapping: DAE metrics -> V2 Observation
        # V2 Observation expects a flexible dict payload.
        # We ensure keys match what BDB aggregator expects (e.g. latency_ms, etc.)
        payload = {
            "latency_ms": m.latency_p95_ms,
            "packet_loss_pct": m.loss_pct,
            # Add other fields as necessary for V2 policy
        }
        
        # Convert float timestamp to datetime
        import datetime
        ts_dt = datetime.datetime.fromtimestamp(m.ts, datetime.timezone.utc)

        obs = Observation(
            ts=ts_dt,
            domain="wifi", # Simplified assumption
            device_id="self-gateway", # M13 didn't have device_id context, adding default
            metrics=payload
        )
        obs_list.append(obs)

    # 2. Summarize (Aggregation)
    # We create a temporary aggregator to summarize this batch
    wm = WindowManager(window_seconds=300) 
    agg = WindowAggregator(wm)
    summary = agg.summarize(obs_list)

    # 3. Compute Code (V2 Core)
    # This ensures our 'lite' code matches the rigorous V2 definition
    result = compute_fp_lite(summary)

    return result.model_dump()

def fp_lite_from_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recalculates fp_lite from a bundle's timeline points.
    Useful for verification or offline analysis.
    """
    # Extract points from legacy or new structure
    points = bundle.get("timeline", {}).get("metrics_points", [])
    
    # Convert to Observation (similar logic)
    obs_list = []
    for p in points:
        # Handle dict input
        payload = {
            "latency_ms": p.get("latency_p95_ms"), # Mapping p95 to latency_ms for V2 agg
            "packet_loss_pct": p.get("loss_pct"),
            "wan_sinr_db": p.get("wan_sinr_db")
        }
        # Mock timestamp if missing, or parse ISO
        import datetime
        ts_str = p.get("t")
        if ts_str:
            ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            ts = datetime.datetime.now(datetime.timezone.utc)
            
        obs = Observation(
            ts=ts,
            domain="wifi", 
            device_id="offline_cli",
            metrics=payload
        )
        obs_list.append(obs)
        
    wm = WindowManager(window_seconds=300) 
    agg = WindowAggregator(wm)
    summary = agg.summarize(obs_list)
    result = compute_fp_lite(summary)
    return result.model_dump()
