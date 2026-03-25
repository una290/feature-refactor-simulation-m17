import requests
import json
import time

BASE_URL = "http://localhost:8000"

def run_scenario(name, context, device_refs, description):
    print(f"\n{'='*60}")
    print(f"🎬 劇本: {name}")
    print(f"📄 說明: {description}")
    print(f"   [Input] Context: {context}")
    print(f"   [Input] Device Refs: {device_refs}")
    print("-" * 60)
    
    payload = {
        "context": context,
        "device_refs": device_refs
    }
    
    try:
        response = requests.post(f"{BASE_URL}/obh/trigger", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            bundle = data.get("bundle", {})
            evidence_grade = bundle.get("evidence_grade", "UNKNOWN")
            missing_req = bundle.get("upgrade_requirements_ref")
            
            # 判斷 pc_priv 是否被攔截 (是否為 null)
            pc_priv = bundle.get("pc_priv")
            is_priv_blocked = "是 (Blocked, payload is null)" if pc_priv is None else "否 (Granted, payload is visible)"
            
            print(f"✅ [結果] Access Grade: {evidence_grade}")
            print(f"🔒 [隱私] 詳細證據 (PC-Priv) 是否被攔截: {is_priv_blocked}")
            
            if missing_req:
                print(f"⚠️ [補救指示] 缺少需求 (Upgrade Requirement): {missing_req}")
        else:
            print(f"❌ API 請求失敗: HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 連線失敗！請確保 server.py (FastAPI) 已經啟動在 http://localhost:8000")

def main():
    print("🚀 BREL v2 隱私治理 4 大情境自動展示腳本\n")
    
    # 劇本 1：Happy Path
    run_scenario(
        name="標準客服收案 (The Happy Path)",
        context="SUPPORT_CLOSURE",
        device_refs={"policy": "tok_v2_ok", "disclosure": "tok_scope_ok"},
        description="用途正確，且設備攜帶了完整的政策與揭露 Token"
    )
    
    time.sleep(1)
    
    # 劇本 2：Legal Block
    run_scenario(
        name="法遵阻擋 - 待簽署 (The Legal Block)",
        context="DISPUTE",
        device_refs={"policy": "tok_v2_ok", "disclosure": "tok_scope_ok"},
        description="用途為爭議處理，依法規需要使用者 App 端簽名，目前尚未簽名"
    )
    
    time.sleep(1)
    
    # 劇本 3：Config Sync Failure (轉圜方案 A 測試)
    run_scenario(
        name="技術指針遺失 (The Config Sync Failure - 轉圜方案A)",
        context="SUPPORT_CLOSURE",
        device_refs={"random_token": "useless_token"},
        description="用途正確，設備漏帶 Policy，但系統套用 Implicit Policy 放行並給予警告"
    )
    
    time.sleep(1)
    
    # 劇本 4：Unauthorized Access
    run_scenario(
        name="惡意越權調閱 (Unauthorized Access)",
        context="MARKETING_ANALYSIS",
        device_refs={"policy": "tok_v2_ok", "disclosure": "tok_scope_ok"},
        description="即使設備端 Token 齊全，但調閱的用途不在業務白名單內"
    )

if __name__ == "__main__":
    main()
