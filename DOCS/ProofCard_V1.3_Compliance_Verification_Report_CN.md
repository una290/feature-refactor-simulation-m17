# V1.3 合規性驗證報告 (Sections 8 & 9)

本文件詳述了針對「DAE ProofCard Free on CPE V1.3」規格書中 **第 8 節 (模擬場景)** 與 **第 9 節 (合規檢查表)** 的驗證流程與結果。

## 1. 合規測試策略
為了確保嚴格符合規格書對於「可重現模擬 (Reproducible Simulation)」的要求，我們實作了一套確定性的離線測試流程：
- **測試數據**: 建立了精確的 JSON 資料集，包含與第 8 節定義完全相同的數值序列。
- **測試引擎**: 使用 `M13.fp_lite_from_bundle` 將這些數據輸入至實際的生產環境程式碼中運算。
- **斷言驗證**: 驗證輸出之 `p50`, `p95`, `verdict` (裁決), 與 `reason_code` (原因碼) 是否與規格書完全一致。

## 2. 模擬結果 (第 8 節)

### 8.1 Wi-Fi 7/8 安裝窗 (Install Window)
*   **場景**: 尾端延遲爆發 (Late-tail latency spike)。
*   **輸入**: N=12 個樣本 (`[20, 22, ... 120]`)。
*   **結果**:
    *   `rtt_ms_p50`: **25 ms** (預期: 25)
    *   `rtt_ms_p95`: **120 ms** (預期: 120)
    *   裁決 (Verdict): **NOT_READY** (使用 Profile: `WIFI78_INSTALL_ACCEPT`)
    *   原因碼: `P95_RTT_TOO_HIGH`
*   **狀態**: ✅ **通過 (PASS)**

### 8.2 FWA 晚高峰擁塞 (Peak Congestion)
*   **場景**: 5G 尾端 RTT 擁塞。
*   **輸入**: N=20 個樣本 (`[35, ... 210]`)。
*   **結果**:
    *   `rtt_ms_p50`: **52 ms** (預期: 52)
    *   `rtt_ms_p95`: **180 ms** (預期: 180)
    *   裁決 (Verdict): **NOT_READY** (使用 Profile: `FWA_CONGESTION_SUSPECT`)
    *   原因碼: `TAIL_RTT_TOO_HIGH`
*   **狀態**: ✅ **通過 (PASS)**

### 8.3 Cable 上行間歇性斷線 (Upstream Intermittent)
*   **場景**: 因 T3/T4 逾時導致的上行 RTT 尖峰。
*   **輸入**: N=40 個樣本 (`[20, ... 220]`)。
*   **結果**:
    *   `us_rtt_ms_p50`: **35 ms** (預期: 35)
    *   `us_rtt_ms_p95`: **200 ms** (預期: 200)
    *   裁決 (Verdict): **NOT_READY** (使用 Profile: `CABLE_UPSTREAM_INTERMITTENT`)
    *   原因碼: `TAIL_US_RTT_TOO_HIGH`
*   **狀態**: ✅ **通過 (PASS)**

## 3. 合規檢查表 (第 9 節)
系統已通過針對「Free-tier CPE」的合規要求檢查：
1.  **ProofCard 產出**: ✅ 每次判定皆產生 ProofCard (經 `ProofCardGenerator` 驗證)。
2.  **必填欄位**: ✅ 包含 `reason_code`, `outcome_facet`, `validity_verdict`, `manifest_ref`。
3.  **Manifest 可信度**: ✅ 確認 Manifest 能查詢並反映持久化的 SQLite 事件儲存。
4.  **計算基準一致性**: ✅ p50/p95 計算邏輯確認符合 `basis_ref` 定義之 Nearest-Rank 算法。

## 4. 如何重現
請執行自動化合規測試腳本：
```bash
python tests/test_v1_3_compliance.py
```
預期輸出：
```
ALL COMPLIANCE TESTS PASSED.
```
