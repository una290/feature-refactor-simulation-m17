
from __future__ import annotations
from typing import List, Dict, Any, Optional
import datetime
import yaml
import os

from .M00_common import (
    EpisodeRecognition, MetricSample, ChangeEventCard, 
    ObservabilityResult, iso
)
from .M09_episode_manager import EpisodeManager

# V2 Core Imports
from .vendors.bdb_proof.core.admission import AdmissionGate, AdmissionRequest
from .vendors.bdb_proof.core.windowing import WindowManager, WindowRef
from .vendors.bdb_proof.core.aggregator import WindowAggregator
from .vendors.bdb_proof.core.boundary import BoundaryEngine
from .vendors.bdb_proof.core.types import (
    Observation, CaseContext, AttemptMeta, SnapshotRefs
)

class RecognitionEngine:
    """
    V2 Adapter Implementation.
    Wraps 'bdb_proof' core components to drive recognition.
    """
    def __init__(self, config_path: str = None):
        self.ep_mgr = EpisodeManager()
        
        # Load V2 Policy
        if config_path is None:
            # Default to vendored config
            base = os.path.dirname(__file__)
            config_path = os.path.join(base, "vendors", "bdb_proof", "configs", "default_policy.yaml")
            
        with open(config_path, "r") as f:
            self.policy = yaml.safe_load(f)

        # Initialize V2 Core Components
        self.wm = WindowManager(window_seconds=300)
        self.agg = WindowAggregator(self.wm)
        self.boundary = BoundaryEngine(self.policy) # Pass full policy
        self.gate = AdmissionGate(self.policy, self.wm, self.agg, self.boundary)

    def recognize(self, latest_metric: MetricSample,
                  recent_change_events: List,
                  worst_window_ref: str) -> EpisodeRecognition:
        
        # 1. Convert DAE Input -> BDB Observation
        # We assume latest_metric is the 'trigger' or the last point of the window
        # For simplicity in this adapter, we might just feed this one point if it's real-time,
        # but ideally we should have fed points continuously.
        # Here we assume 'recognize' is called at the end of a window with a backlog.
        
        # NOTE: In a real integration, we should be feeding observations continuously.
        # For this DAE P1 adapter, we map the single sample to maintain API signature,
        # but the AdmissionGate really needs a history.
        # We will act as if we just received this point.
        
        payload = {
            "latency_ms": latest_metric.latency_p95_ms, # Mapped from p95
            "packet_loss_pct": latest_metric.loss_pct, # Mapped from loss_pct
            "wan_status": "up" # simplified
        }
        # Convert float timestamp to datetime
        ts_dt = datetime.datetime.fromtimestamp(latest_metric.ts, datetime.timezone.utc)
        
        obs = Observation(
            ts=ts_dt,
            domain="wifi", # Simplified assumption
            device_id="self-gateway",
            metrics=payload
        )
        
        # 2. Feed to Aggregator
        # This updates the internal state of the current window
        wref_obj = self.agg.add(obs)
        
        # 3. Construct Admission Request
        # This asks the Gate: "Can we admit this window/episode?"
        req = AdmissionRequest(
            case=CaseContext(
                device_id="self-gateway",
                case_id=f"case_{int(ts_dt.timestamp())}"
            ),
            attempt=AttemptMeta(
                origin_ref="dae_p1_periodic",
                attempt_id=f"att_{int(ts_dt.timestamp())}"
            ),
            snapshot_refs=SnapshotRefs(
                policy_snapshot_ref="pol_def",
                version_ref="v2_adapter"
            )
        )
        
        # 4. Execute Decision (The V2 Brain)
        # return_bundle=True means we get the full EvidenceBundle
        bundle = self.gate.decide(req, window_id=wref_obj.window_id)
        
        # 5. Map Output (BDB Bundle -> DAE EpisodeRecognition)
        # We maintain the EpisodeManager to generate consistent IDs
        # but the verdict now comes from BDB.
        
        # Interpret BDB verdict to legacy DAE verdict
        # BDB: PERMIT, DENY, DEGRADE, COOLDOWN
        # DAE: WAN_UNSTABLE, WIFI_CONGESTION, etc.
        # Use reason codes to map back if needed, or default to generic.
        
        legacy_verdict = "UNKNOWN"
        if bundle.admission_verdict == "DENY":
            legacy_verdict = "OPAQUE_RISK" # Example mapping
        elif bundle.admission_verdict == "PERMIT":
            # Check reasons for specifics
            if "WAN_LATENCY" in bundle.reason_codes:
                legacy_verdict = "WAN_UNSTABLE"
        
        # Get episode state from manager
        ep = self.ep_mgr.start_or_update(
            worst_window_ref=worst_window_ref,
            evidence_ref=bundle.evidence_id
        )
        
        # Observability from BDB Readiness
        obs_res = ObservabilityResult(
            observability_status="SUFFICIENT" if bundle.readiness.readiness == "SUFFICIENT" else "INSUFFICIENT",
            opaque_risk=(bundle.readiness.readiness == "INSUFFICIENT"),
            missing_refs=bundle.readiness.missing_fields,
            origin_hint="bdb_core"
        )
        
        curr_conf = 0.9 if bundle.admission_verdict != "QUARANTINE" else 0.1

        return EpisodeRecognition(
            episode_id=ep.episode_id,
            episode_start=ep.start_ts,
            worst_window_ref=ep.worst_window_ref,
            primary_verdict=legacy_verdict, # Or map from bundle.triage
            confidence=curr_conf,
            evidence_refs=ep.evidence_refs[-10:],
            observability=obs_res,
            bdb_bundle=bundle.model_dump(mode='json')
        )
