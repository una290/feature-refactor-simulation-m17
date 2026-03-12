# DAE P1 (19 Modules) 全模組參數字典 (All Modules Parameters Dictionary)
**版號：** V1.4
**說明：** 本份文件取代舊版的 PC-Min 細節文件，基於最新 V1.4 程式碼（包含 `M00_common`, `M13_fp_lite`, `M20_install_verify`, `M22_privacy_governance` 等核心模組），彙整合併了四大層級的輸入、驗證、證據生成與隱私審閱欄位。

---

## 📥 1. 資料輸入層 (Metrics & Adapter - `M00_common.MetricSample`)
來自底層設備 (如 Wi-Fi 路由器或 Cable Edge Modem) 的第一手遙測數值。

| 欄位名稱 | 當前結果 (型態範例) | 可能結果 (列舉值) | 判斷依據 (程式邏輯) | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| `domain` | `"CABLE"` (str) | `"WIFI"`, `"CABLE"` | 設備來源標籤 | 決定後續 M20 和 M13 要套用哪個 Profile 驗證規則 |
| `ts` | `1709400000.0` (float) | UNIX Timestamp | Adapter 解析寫入 | 該筆樣本發生的時間點 |
| `latency_p95_ms` | `45.2` (float) | `0.0` \~ `>1000.0` | 設備回報或 Adapter 計算 | 網路延遲的第 95 百分位數 (Wi-Fi 側為主) |
| `loss_pct` | `0.5` (float) | `0.0` \~ `100.0` | 設備回報 | 封包遺失率百分比 |
| `retry_pct` | `12.0` (float) | `0.0` \~ `100.0` | 設備回報 | Wi-Fi 傳輸重試率 (高代表干擾或擁塞) |
| `signal_strength_pct` | `85` (int) | `0` \~ `100` | 設備回報 | 綜合無線訊號強度 |
| `wan_rsrp_dbm` | `-95.0` (float) | `-140.0` \~ `-40.0` | 設備回報 | 針對 FWA/5G 的接收訊號強度指標 |
| `wan_sinr_db` | `15.0` (float) | `-10.0` \~ `40.0` | 設備回報 | 針對 FWA/5G 的訊號雜訊比 |
| `us_latency_p95_ms` | `25.5` (float) | `0.0` \~ `>1000.0` | 設備回報 | 針對 Cable 專用的上行方向延遲 |
| `ofdm_mer_db` | `35.2` (float) | `10.0` \~ `50.0` | 設備回報 | 針對 Cable 專用的正交頻分多工調變誤差比 |
| `t3_count` / `t4_count` | `2` (int) | `0` \~ 無上限 | 設備回報 | 針對 Cable 的 T3/T4 Timeout 異常計數 |
| `fec_corrected` | `60` (int) | `0` \~ 無上限 | 設備回報 | 可修正的前向錯誤更正 (FEC) 計數，過高代表線路雜訊 |
| `fec_uncorrected` | `5` (int) | `0` \~ 無上限 | 設備回報 | 不可修正的 FEC 錯誤，導致掉包的直接元凶 |
| `dns_status` | `"OK"` (str) | `"OK"`, `"FAIL"`, `"UNKNOWN"` | 設備 DNS 解析測試 | M20 驗證時若為 FAIL 直接判斷為 WAN 異常 |

---

## 🕵️‍♂️ 2. 狀態驗證層 (Install Verifier - `M20_install_verify`)
用來瞬間判斷該區間數據是否達標的檢測結果。

| 欄位名稱 | 當前結果 (型態範例) | 可能結果 (列舉值) | 判斷依據 (程式邏輯) | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| `readiness_verdict` | `"FAIL"` (str) | `"PASS"`, `"MARGINAL"`, `"FAIL"` | `M13` Profile 條件比對 | 判斷該安裝或時段是否達標 (無任何 ReasonCode 則為 PASS) |
| `closure_readiness` | `"not_ready"` (str) | `"ready"`, `"not_ready"` | 依賴 `readiness_verdict` | 若 verdict 為 PASS 則 ready，否則 not_ready |
| `dominant_factor` | `"PLANT_IMPAIRMENT"` (str) | `"WAN", "WIFI", "OPAQUE", "UNKNOWN", 或 ReasonCode` | 獲取首個失敗的 reason code 或 DNS 狀態 | 標示導致驗證失敗的最主要因子 |
| `confidence` | `0.85` (float) | `0.0` \~ `1.0` | 樣本數量與結果加成 | 預設視結果給予 0.8 或 0.85，若樣本 > 18 筆再 +0.1 |

---

## 🪪 3. 證據生成層 (ProofCard / PC-Min - `M13_fp_lite`)
當觸發 OBH (一鍵產出) 或要求出示證據包時，所形成的最終事實紀錄。

| 欄位名稱 | 當前結果 (型態範例) | 可能結果 (列舉值) | 判斷依據 (程式邏輯) | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| `status` | `"NOT_READY"` (str) | `"READY"`, `"NOT_READY"`, `"INSUFFICIENT_EVIDENCE"` | 檢查 `reasons` 是否為空或樣本不足 | ProofCard 本身的整備狀態 |
| `diagnosis_code` | `"WIFI_CONGESTION"` (str) | `"WAN_UNSTABLE", "WIFI_CONGESTION", "MESH_FLAP", "UNKNOWN"` 等 | 基於 M13 傳回的錯誤代碼推導 | 該證據卡總結的異常根本原因分類 |
| `reason_code` | `["T3T4_RETRY_BURST"]` (List[str]) | `"P95_RTT_TOO_HIGH", "PLANT_IMPAIRMENT_SUSPECT", "LOW_PHY_RATE"`... | Profiler 掃描每項 Threshold 突破時記錄 | 列出所有未達標的具體量測項目代碼 |
| `validity_grade` | `"DELIVERY_GRADE"` (str) | `"DELIVERY_GRADE"`, `"CLOSURE_GRADE"`, `"UNKNOWN"` | 預設為 DELIVERY，經 M22 BYUSE 校驗後決定 | 此證據卡可被採信的法律與合約位階 |
| `health_checks` | `[{...}]` (List[CheckResult]) | `[{name, threshold, actual, status, reason}]` | `ProfileBase.check()` 結果陣列 | 詳細條列 Threshold 的過關/失敗細節 |
| `outcome_facet` | `[{"name": "rtt_p95",...}]` (List[Dict]) | 包含指標名稱、數值、單位的字典清單 | 抽取最關鍵的指標 (FAILED 時取 p95) | 呈現於 UI 面板上的關鍵指標數值摘要 |
| `missing_evidence_class`| `["PRIVACY_POLICY_MISSING"]` | 空陣列或各類型 missing class string | 在 `M22` Base Validity Hook 中檢查 | 記載缺少了什麼要件導致證據無法完整 |

---

## 🛡️ 4. 隱私稽核層 (Privacy Governance / PC-Priv - `M22_privacy_governance`)
掌控權限、視野與資料脫敏的機密級管制。

| 欄位名稱 | 當前結果 (型態範例) | 可能結果 (列舉值) | 判斷依據 (程式邏輯) | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| `observability_status`| `"SUFFICIENT"` (str) | `"SUFFICIENT"`, `"INSUFFICIENT"` | 先驗遙測視野是否被截斷 | 標示此設備是否有足夠的底層權限可觀測問題 |
| `opaque_risk` | `False` (bool) | `True`, `False` | 判斷是否有黑箱設備阻擋探測 | 是否處於 Opaque Data 階段 |
| `policy_valid` | `True` (bool) | `True`, `False` | `check_base_validity()` 判定 | 附加在 `refs` 中的 flag，指示此卡是否合法合規 |
| `egress_receipt_ref` | `"EGRESS-REC-a1b2c3d4"` | `"EGRESS-REC-..."`, `None` | `project_view()` 判斷 Request Scope | 只有當獲准匯出 Sensitive Payload 時才會核發的收據碼 |
| `gate_ref` | `"EG-DEFAULT-V1"` (str) | `"EG-STRICT-V2"`, `"EG-DEFAULT-V1"` | 根據 `strict_mode` 開關設定 | 當前套用的 Egress (匯出) 守門規則版本 |
| `payload` | `{...}` 或 `None` | `Dict` / `None` | `authority_scope_ref` 權限對接 | 完整的時間軸與除錯深度矩陣資料，若全線被阻擋則直接以 `None` 輸出不顯示 |

---

## 🗺️ 5. 診斷對應表 (Diagnosis Mapping Table - `DIAGNOSIS_MAP`)
用於將具體的底層錯誤代碼 (`ReasonCode`) 翻譯為高階的客戶端/客服端大類別 (`Verdict / Diagnosis_Code`)。

| M13 底層原因碼 (ReasonCode) | -> 翻譯結果 | 高階診斷大類 (Diagnosis Code) | 觸發情境說明 |
| :--- | :---: | :--- | :--- |
| **`INSUFFICIENT_SAMPLES`** | -> | **`UNKNOWN`** | 樣本數不足，無法判定 |
| **`PASSED_ALL_CHECKS`** | -> | **`HEALTHY`** | 所有指標皆通過檢測，設備健康 |
| **[Wi-Fi 7/8 系列]** | | | |
| `P95_RTT_TOO_HIGH` | -> | `WAN_UNSTABLE` | 延遲過高，歸咎於上游 WAN 網路不穩 |
| `P95_LOSS_TOO_HIGH` | -> | `WAN_UNSTABLE` | 嚴重掉包，歸咎於上游 WAN 網路不穩 |
| `WIFI_SIDE_OSCILLATION` | -> | `WIFI_CONGESTION` | Wi-Fi 封包重傳率高，通常是頻道擁塞或干擾 |
| `LOW_PHY_RATE` | -> | `WIFI_CONGESTION` | 設備連線的實體協商速率過低 |
| `MESH_BACKHAUL_LIMITER` | -> | `MESH_FLAP` | Mesh 節點間的回傳訊號強度不足 |
| `MLO_ASYMMETRIC_LINK` | -> | `WIFI_CONGESTION` | MLO 多重連接狀態不對稱 (Wi-Fi 7 特有) |
| **[FWA / 5G 系列]** | | | |
| `WEAK_COVERAGE_RSRP_P5` | -> | `FWA_SIGNAL_WEAK` | 5G/LTE 接收訊號強度指標過低 |
| `LOW_SINR_P5` | -> | `FWA_SIGNAL_WEAK` | 5G/LTE 訊號雜訊比過低 |
| `CELL_RESELECT_UNSTABLE` | -> | `WAN_UNSTABLE` | 設備頻繁在不同基地台之間跳換 |
| `TAIL_RTT_TOO_HIGH` | -> | `WAN_UNSTABLE` | 5G/LTE 尾端延遲過高 |
| `PEAK_CONGESTION_SUSPECT` | -> | `WAN_UNSTABLE` | 疑似遭遇基地台尖峰時段擁塞 |
| **[Cable / DOCSIS 系列]** | | | |
| `T3T4_RETRY_BURST` | -> | `CABLE_PLANT_ISSUE` | 發生 T3 或 T4 Timeout 連線重試爆發 |
| `TAIL_US_RTT_TOO_HIGH` | -> | `CABLE_PLANT_ISSUE` | Cable 上行方向延遲異常飆高 |
| `TAIL_US_LOSS_TOO_HIGH` | -> | `CABLE_PLANT_ISSUE` | Cable 上行方向發生掉包 |
| `PLANT_IMPAIRMENT_SUSPECT` | -> | `CABLE_PLANT_ISSUE` | OFDM MER 過低或 FEC 錯誤修正爆量，疑似實體線路異常 |
