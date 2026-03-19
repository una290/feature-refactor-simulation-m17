import sys
import os
import uuid
import time
from dataclasses import dataclass, asdict

# Ensure we can import from the current directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dae_p1.M12_obh_controller import OBHController
from dae_p1.M11_bundle_exporter import BundleExporter
from dae_p1.M00_common import EpisodeRecognition, ObservabilityResult

def run_test():
    exporter = BundleExporter()
    ctrl = OBHController(exporter)
    
    # Setup dummy data
    rec = EpisodeRecognition(
        episode_id="demo-ep-123",
        episode_start=time.time(),
        worst_window_ref="W-DEMO",
        diagnosis_code="TEST_DIAG",
        confidence=0.95,
        evidence_refs=["ref1"],
        observability=ObservabilityResult("SUFFICIENT", False)
    )
    
    metrics = [{"ts": time.time(), "rtt_ms": 50.0}]
    events = []
    snapshots = []

    print("=== BREL Rich Scenario Verification (V4) ===\n")

    # --- Scenario 1: Happy Path (READY) ---
    print("Scenario 1: Routine Support (Happy Path)")
    res = ctrl.run(
        out_dir="tmp_demo",
        recognition=rec,
        metrics=metrics,
        events=events,
        snapshots=snapshots,
        byuse_context_ref="SUPPORT_CLOSURE",
        authority_scope_ref="isp-support"
    )
    print(f"  Grade: {res.bundle_content['evidence_grade']}")
    print(f"  PC-Priv status: {'OPEN' if res.bundle_content['pc_priv'] else 'STRIPPED'}")
    print("-" * 40)

    # --- Scenario 2: Technology Sync Error (INCOMPLETE) ---
    print("Scenario 2: Device Policy Missing (Sync Error)")
    # We simulate this by manually monkey-patching the card's refs before grading 
    # Or more simply, testing the grading logic directly
    card_missing_policy = {
        "refs": {"disclosure": "tok_scope_isp_support"} # Missing 'policy'
    }
    grade, req = ctrl.governance.evaluate_closure_grade(card_missing_policy, "SUPPORT_CLOSURE")
    print(f"  Grade: {grade}")
    print(f"  Requirement: {req}")
    print("-" * 40)

    # --- Scenario 3: Legal/Consent Gap (PENDING) ---
    print("Scenario 3: Dispute Case - Awaiting Signature (Legal Gap)")
    res_pending = ctrl.run(
        out_dir="tmp_demo",
        recognition=rec,
        metrics=metrics,
        events=events,
        snapshots=snapshots,
        byuse_context_ref="DISPUTE",
        authority_scope_ref="isp-support"
    )
    print(f"  Grade: {res_pending.bundle_content['evidence_grade']}")
    print(f"  PC-Priv status: {'OPEN' if res_pending.bundle_content['pc_priv'] else 'STRIPPED'}")
    
    print("\n  User signs the manifest in App...")
    ctrl.signed_manifests.add(rec.episode_id)
    
    res_ready = ctrl.retrieve_bundle(rec.episode_id, byuse_context_ref="DISPUTE", authority_scope_ref="isp-support")
    print(f"  Grade after signature: {res_ready['evidence_grade']}")
    print(f"  PC-Priv status: {'OPEN' if res_ready['pc_priv'] else 'STRIPPED'}")
    print("-" * 40)

    # --- Scenario 4: Access Policy Guard (UNAUTHORIZED) ---
    print("Scenario 4: Invalid/Missing Context (Security Guard)")
    res_unauth = ctrl.run(
        out_dir="tmp_demo",
        recognition=rec,
        metrics=metrics,
        events=events,
        snapshots=snapshots,
        byuse_context_ref="UNKNOWN_REASON",
        authority_scope_ref="isp-support"
    )
    print(f"  Grade: {res_unauth.bundle_content['evidence_grade']}")
    print(f"  PC-Priv status: {'OPEN' if res_unauth.bundle_content['pc_priv'] else 'STRIPPED'}")
    print("-" * 40)

if __name__ == "__main__":
    run_test()
