
import json
import sys
import shutil
from dae_p1.M12_obh_controller import OBHController
from dae_p1.M11_bundle_exporter import BundleExporter
from dae_p1.M00_common import EpisodeRecognition, ObservabilityResult

def verify_obh_fix():
    print("--- Verifying M12 Fix for Evidence Grade ---")
    
    # 1. Setup Controller
    exporter = BundleExporter()
    ctrl = OBHController(exporter)
    
    # 2. Mock Recognition/Inputs
    rec = EpisodeRecognition(
        episode_id="test-ep-1",
        episode_start=1234567890.0,
        worst_window_ref="W-TEST",
        primary_verdict="UNKNOWN",
        confidence=1.0,
        evidence_refs=[],
        observability=ObservabilityResult("SUFFICIENT", False)
    )
    
    # 3. Running Controller
    # Pass minimal inputs
    res = ctrl.run(
        out_dir="out/test_verify", 
        recognition=rec, 
        metrics=[], 
        events=[], 
        snapshots=[],
        authority_scope_ref="isp-support" # Authorized
    )
    
    # 4. Check Bundle Content
    v13_card = res.bundle_content.get("proof_card_v13")
    if not v13_card:
        print("FAIL: proof_card_v13 missing from bundle!")
        return

    grade = v13_card.get("evidence_grade")
    print(f"Extracted Grade from V1.3 shim: {grade}")
    
    if grade == "DELIVERY_GRADE":
        print("PASS: Grade is present and correct.")
    else:
        print(f"FAIL: Grade is {grade}, expected DELIVERY_GRADE")

    adm = v13_card.get("admission_verdict")
    print(f"Extracted Adm from V1.3 shim: {adm}")
    
    if adm == "ADMIT":
        print("PASS: Admission is present and correct.")
    else:
        print(f"FAIL: Admission is {adm}, expected ADMIT")

if __name__ == "__main__":
    verify_obh_fix()
