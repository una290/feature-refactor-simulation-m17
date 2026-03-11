import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from fastapi.testclient import TestClient
import server

# Override the adapter based on test type
def setup_test_server(adapter_type="WIFI"):
    if adapter_type == "CABLE":
        from dae_p1.adapters.DOCSIS_adapter import DOCSISAdapter
        server.adapter = DOCSISAdapter()
    elif adapter_type == "WIFI":
        from dae_p1.adapters.windows_wifi_adapter import WindowsWifiAdapter
        server.adapter = WindowsWifiAdapter()
        
    from dae_p1.core_service import OBHCoreService, CoreRuntimeConfig
    from dae_p1.M21_manifest_manager import ManifestManager
    cfg = CoreRuntimeConfig(sample_interval_sec=1, buffer_minutes=10, accelerate=True, persistence_enabled=False)
    server.core = OBHCoreService(server.adapter, cfg)
    server.manifest_manager = ManifestManager(server.core.metrics_buf, server.core.events_buf)
    
    # Tick a few times to simulate data collection
    for _ in range(15):
        server.core.tick_once()

client = TestClient(server.app)

def test_api(adapter_type):
    print(f"\n--- Testing API with {adapter_type} Adapter ---")
    setup_test_server(adapter_type)
    
    # Test /install_verify
    res = client.get("/install_verify")
    data = res.json()
    sys_info = data.get("system_info", {})
    thresholds = data.get("thresholds", {})
    print(f"1. /install_verify API Domain: {sys_info.get('domain')}")
    print(f"   Profile evaluated: {thresholds.get('profile_ref')}")
    
    # Test /device/local/proof
    res2 = client.get("/device/local/proof")
    data2 = res2.json()
    profile_ref = data2.get("profile_ref", "Unknown")
    print(f"2. /device/local/proof API Profile Used: {profile_ref}")
    
    # Test /obh/trigger
    res3 = client.post("/obh/trigger")
    if res3.status_code == 200:
        ep_id = res3.json().get("episode_id")
        print(f"3. /obh/trigger API Episode ID generated: {ep_id}")
    else:
        print(f"3. /obh/trigger API failed: {res3.text}")

if __name__ == "__main__":
    test_api("WIFI")
    test_api("CABLE")
