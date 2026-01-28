
import json
import os
import sys

# Ensure we can import dae_p1
sys.path.append(os.path.join(os.getcwd()))

from dae_p1.M13_fp_lite import fp_lite_from_bundle

def verify_scenario(name, bundle_path, expected):
    print(f"--- Verifying Scenario: {name} ---")
    with open(bundle_path, 'r', encoding='utf-8') as f:
        bundle = json.load(f)
    
    result = fp_lite_from_bundle(bundle)
    
    # 1. Check Verdict
    verdict = result.get("verdict")
    if verdict != expected["verdict"]:
        print(f"[FAIL] Verdict mismatch. Expected {expected['verdict']}, got {verdict}")
        return False
        
    # 2. Check Reason Code (if any expected)
    reasons = result.get("reason_code", [])
    if expected["reason_code"] and expected["reason_code"] not in reasons:
         print(f"[FAIL] Reason mismatch. Expected {expected['reason_code']} in {reasons}")
         return False

    # 3. Check p50/p95
    p50_map = {item["name"]: item["value"] for item in result.get("p50", [])}
    p95_map = {item["name"]: item["value"] for item in result.get("p95", [])}
    
    for key, val in expected["p50"].items():
        if p50_map.get(key) != val:
            print(f"[FAIL] p50 mismatch for {key}. Expected {val}, got {p50_map.get(key)}")
            return False
            
    for key, val in expected["p95"].items():
        if p95_map.get(key) != val:
            print(f"[FAIL] p95 mismatch for {key}. Expected {val}, got {p95_map.get(key)}")
            return False
            
    print(f"[PASS] Scenario {name} matched perfectly.")
    return True

def check_section_9_compliance(card):
    print("--- Checking Section 9 Compliance ---")
    must_have = ["proof_card_ref", "verdict", "validity_verdict", "manifest_ref", "reason_code", "outcome_facet"]
    missing = [f for f in must_have if f not in card]
    
    if missing:
        print(f"[FAIL] Missing MUST fields: {missing}")
        return False
        
    if not card["reason_code"]:
        print("[FAIL] reason_code[] must have at least 1 item")
        return False
        
    # outcome_facet must be present (M13 populates it)
    if not card["outcome_facet"]:
        print("[FAIL] outcome_facet[] must have at least 1 item")
        return False
        
    print("[PASS] Section 9 Checklist Passed.")
    return True

def main():
    base_dir = "tests/compliance_data"
    
    # Scenario 8.1
    s1 = verify_scenario("8.1 Wi-Fi", os.path.join(base_dir, "scenario_8_1_wifi.json"), {
        "verdict": "NOT_READY",
        "reason_code": "P95_RTT_TOO_HIGH",
        "p50": {"rtt_ms_p50": 25.0},
        "p95": {"rtt_ms_p95": 120.0}
    })
    
    # Scenario 8.2
    s2 = verify_scenario("8.2 FWA", os.path.join(base_dir, "scenario_8_2_fwa.json"), {
        "verdict": "NOT_READY",
        "reason_code": "TAIL_RTT_TOO_HIGH",
        "p50": {"rtt_ms_p50": 52.0},
        "p95": {"rtt_ms_p95": 180.0}
    })
    
    # Scenario 8.3
    s3 = verify_scenario("8.3 Cable", os.path.join(base_dir, "scenario_8_3_cable.json"), {
        "verdict": "NOT_READY",
        "reason_code": "TAIL_US_RTT_TOO_HIGH",
        "p50": {"us_rtt_ms_p50": 35.0},
        "p95": {"us_rtt_ms_p95": 200.0}
    })
    
    # Load one result for Sec 9 check
    with open(os.path.join(base_dir, "scenario_8_1_wifi.json"), 'r') as f:
        card = fp_lite_from_bundle(json.load(f))
    s9 = check_section_9_compliance(card)

    if s1 and s2 and s3 and s9:
        print("\nALL COMPLIANCE TESTS PASSED.")
    else:
        print("\nSOME TESTS FAILED.")

if __name__ == "__main__":
    main()
