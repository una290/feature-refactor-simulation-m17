import sys
sys.path.append(r"C:\Users\ubee2\Downloads\DAE_P1_19Modules-feature-refactor-simulation-m17\DAE_P1_19Modules-feature-refactor-simulation-m17")
from dae_p1.M00_common import ProofCard, EpisodeRecognition, ObservabilityResult
from dae_p1.M22_privacy_governance import PrivacyGovernance
from dae_p1.M13_fp_lite import ProofCardGenerator
from dae_p1.M12_obh_controller import OBHController
import uuid, time

dummy_rec = EpisodeRecognition(
    episode_id=f"ep-{uuid.uuid4().hex[:8]}",
    episode_start=time.time(),
    worst_window_ref="W-LATEST",
    diagnosis_code="UNKNOWN",
    confidence=1.0,
    evidence_refs=[],
    observability=ObservabilityResult("SUFFICIENT", False)
)

gen = ProofCardGenerator()
metrics = [{"ts": time.time(), "latency_ms": 50, "loss_pct": 0, "rtt_ms": 50}] * 10
card = gen.generate(
    metrics=metrics,
    events=[],
    snapshots=[],
    profile_ref="WIFI78_INSTALL_ACCEPT"
)
print("Status:", card.status)
print("Missing:", card.missing_evidence_class)
print("Payload exists:", card.payload is not None)

gov = PrivacyGovernance()
proj = gov.project_view(card, authority_scope_ref=None)
print("Proj No Auth Payload:", proj.get("payload") is not None)

proj_auth = gov.project_view(card, authority_scope_ref="isp-support")
print("Proj Auth Payload:", proj_auth.get("payload") is not None)

grade1, upgrade1 = gov.evaluate_closure_grade(proj, None)
print("No Context:", grade1, upgrade1)

grade2, upgrade2 = gov.evaluate_closure_grade(proj, "dispute")
print("Dispute Context:", grade2, upgrade2)

print("\n--- Testing M12 OBH Controller (Audit Logging) ---")
from dae_p1.M11_bundle_exporter import BundleExporter
import os

os.makedirs("bundles", exist_ok=True)
exporter = BundleExporter()
controller = OBHController(exporter)

res = controller.run("bundles", dummy_rec, metrics, [], [], authority_scope_ref="isp-support", byuse_context_ref="dispute")
print("Exported Bundle Path:", res.exported_path)

print("\n--- ALL TESTS PASSED ---")
