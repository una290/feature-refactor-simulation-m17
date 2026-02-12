import sys
import os
import json
import asyncio

# Ensure project root is in path
sys.path.append(os.getcwd())

from dae_p1.M12_obh_controller import OBHController, OBHResult
from dae_p1.M10_timeline_builder import TimelineBuilder
from dae_p1.M11_bundle_exporter import BundleExporter
from dae_p1.M00_common import EpisodeRecognition, ObservabilityResult, AdmissionVerdict
from dataclasses import dataclass, field

# Mock dependencies
class MockExporter(BundleExporter):
    def export(self, out_dir, episode_id, bundle):
        # Just return the bundle for inspection
        print("DEBUG: Bundle Content Keys:", bundle.keys())
        if "payload" in bundle:
            if isinstance(bundle["payload"], dict):
                print("DEBUG: Payload Keys:", bundle["payload"].keys())
            else:
                print("DEBUG: Payload Content:", bundle["payload"])
        return "mock/path"

class MockValidator:
    def check_unauthorized(self, bundle):
        if "proof_card_v13" in bundle:
            print("FAIL: proof_card_v13 should NOT be in unauthorized bundle")
            return False
        if "REDACTED" not in str(bundle.get("payload")):
            print("FAIL: Payload should be REDACTED")
            return False
        print("SUCCESS: Unauthorized request correctly redacted.")
        return True

    def check_authorized(self, bundle):
        if "proof_card_v13" not in bundle:
            print("FAIL: Authorized bundle missing proof_card_v13")
            return False
        if isinstance(bundle.get("payload"), str): # Redacted string
            print("FAIL: Authorized payload should NOT be redacted")
            return False
        print(f"SUCCESS: Authorized request returned full data. Verdict: {bundle['proof_card_v13'].get('verdict')}")
        return True

async def test_obh_integration():
    print("--- Testing OBH Integration Refactor ---")
    
    # Setup
    exporter = MockExporter()
    controller = OBHController(exporter)
    
    # Mock Data
    rec = EpisodeRecognition(
        episode_id="EP-TEST-001",
        episode_start=1234567890.0,
        worst_window_ref="W-TEST",
        primary_verdict="WAN_UNSTABLE",
        confidence=0.9,
        evidence_refs=["ev-1"],
        observability=ObservabilityResult("SUFFICIENT", False)
    )
    
    # Mock Metrics (M10 expects objects with .ts, M13 expects dicts or objs)
    @dataclass
    class MockMetric:
        ts: float = 0.0
        latency_p95_ms: float = 0.0
        loss_pct: float = 0.0
        retry_pct: float = 0.0
        airtime_busy_pct: float = 0.0
        mesh_flap_count: int = 0
        wan_sinr_db: float = 0.0
        window_ref: str = "unknown"
            
    metrics = [
        MockMetric(ts=100, latency_p95_ms=20, window_ref="w1"),
        MockMetric(ts=101, latency_p95_ms=25, window_ref="w2"),
        MockMetric(ts=102, latency_p95_ms=150, window_ref="w3") # Spike
    ]
    
    validator = MockValidator()

    # TEST 1: Unauthorized
    print("\n[TEST 1] Unauthorized Request...")
    res1 = controller.run("out", rec, metrics, [], [])
    if not validator.check_unauthorized(res1.bundle_content):
        print("TEST 1 FAILED")
        return

    # TEST 2: Authorized
    print("\n[TEST 2] Authorized Request...")
    res2 = controller.run("out", rec, metrics, [], [], authority_scope_ref="isp-support")
    if not validator.check_authorized(res2.bundle_content):
        print("TEST 2 FAILED")
        return

    print("\nALL TESTS PASSED")

if __name__ == "__main__":
    asyncio.run(test_obh_integration())
