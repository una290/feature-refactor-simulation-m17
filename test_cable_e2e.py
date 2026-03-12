from fastapi.testclient import TestClient
import time
import json
import server
from server import app
import asyncio

# Setup client
client = TestClient(app)

def run_tests():
    print("--- STARTING DOCSIS CABLE E2E TESTING ---")
    
    # 1. Switch to Cable Mode using the Demo Override API
    print("\n1. Switching to Cable Domain...")
    resp = client.post("/simulate/incident?type=stable&duration=300&domain=CABLE")
    print(f"Set Domain Response: {resp.status_code}")
    
    # Let the core tick a few times to generate some Mock Cable Samples
    print("Waiting for samples to accumulate (3 seconds)...")
    for _ in range(3):
        server.core.tick_once()
    
    # 2. Check /install_verify
    print("\n2. Checking /install_verify API...")
    resp = client.get("/install_verify")
    data = resp.json()
    
    domain = data.get("system_info", {}).get("domain")
    verdict = data.get("readiness_verdict")
    dominant = data.get("dominant_factor")
    mer = data.get("fp_vector", {}).get("ofdm_mer_db")
    print(f"Domain: {domain}")
    print(f"Readiness: {verdict}")
    print(f"Dominant Factor: {dominant}")
    print(f"OFDM MER DB: {mer}")
    
    assert domain == "CABLE", f"Expected CABLE domain, got {domain}"
    
    # 3. Check OBH ProofCard Generation for mock_cable
    print("\n3. Checking OBH ProofCard Generation...")
    resp = client.get("/device/mock_cable/proof")
    proof_data = resp.json()
    print("PROOF_DATA RESPONSE:", json.dumps(proof_data, indent=2))
    
    engineering_proof = proof_data.get("payload", {}).get("engineering_proof", {})
    profile_ref = engineering_proof.get("profile_ref")
    health_checks = engineering_proof.get("health_checks", [])
    
    print(f"Profile: {profile_ref}")
    check_names = [c["name"] for c in health_checks]
    print(f"Health Checks: {check_names}")
    
    assert profile_ref == "CABLE_INSTALL_ACCEPT", f"Expected CABLE Profile, got {profile_ref}"
    assert any("MER" in n for n in check_names), "Expected OFDM MER check in health logic."

    print("\n--- ALL TESTS PASSED! THE LOGIC IS FULLY INTEGRATED ---")

if __name__ == "__main__":
    with client:
        run_tests()
