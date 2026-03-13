# DAE P1 (19 Modules) 全模組參數字典 (All Modules Parameters Dictionary)
**版號：** V1.4
**說明：** 本份文件取代舊版的 PC-Min 細節文件，基於最新 V1.4 程式碼（包含 `M00_common`, `M13_fp_lite`, `M20_install_verify`, `M22_privacy_governance` 等核心模組），彙整合併了四大層級的輸入、驗證、證據生成與隱私審閱欄位。

---

## 📥 1. 資料輸入層 (Metrics & Adapter - `M00_common.MetricSample`)
來自底層設備 (如 Wi-Fi 路由器或 Cable Edge Modem) 的第一手遙測數值。

### 1A. 通用與 Wi-Fi 路由器參數 (General & Wi-Fi Router)
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
| `dns_status` | `"OK"` (str) | `"OK"`, `"FAIL"`, `"UNKNOWN"` | 設備 DNS 解析測試 | M20 驗證時若為 FAIL 直接判斷為 WAN 異常 |

### 1B. Cable 數據機專用參數 (Cable Edge Modem)
| 欄位名稱 | 當前結果 (型態範例) | 可能結果 (列舉值) | 判斷依據 (程式邏輯) | 說明 |
| :--- | :--- | :--- | :--- | :--- |
| `us_latency_p95_ms` | `25.5` (float) | `0.0` \~ `>1000.0` | 設備回報 | 針對 Cable 專用的上行方向延遲 |
| `ofdm_mer_db` | `35.2` (float) | `10.0` \~ `50.0` | 設備回報 | 針對 Cable 專用的正交頻分多工調變誤差比 |
| `t3_count` / `t4_count` | `2` (int) | `0` \~ 無上限 | 設備回報 | 針對 Cable 的 T3/T4 Timeout 異常計數 |
| `fec_corrected` | `60` (int) | `0` \~ 無上限 | 設備回報 | 可修正的前向錯誤更正 (FEC) 計數，過高代表線路雜訊 |
| `fec_uncorrected` | `5` (int) | `0` \~ 無上限 | 設備回報 | 不可修正的 FEC 錯誤，導致掉包的直接元凶 |

---

## 🕵️‍♂️ 2. 狀態驗證層 (Install Verifier - `M20_install_verify`)
用來瞬間判斷該區間數據是否達標的檢測結果。

```mermaid
graph TD
    A[Start M20 Verification] --> B{DNS Status OK?}
    B -- FAIL --> C[readiness_verdict = FAIL]
    C --> D[dominant_factor = 'WAN (DNS)']
    B -- OK --> E{Check M13 Profile Thresholds}
    E -- All PASS --> F[readiness_verdict = PASS]
    F --> G[closure_readiness = ready]
    E -- Any FAIL --> H[readiness_verdict = FAIL]
    H --> I[closure_readiness = not_ready]
    I --> J[dominant_factor = First ReasonCode Translation]
```

### 欄位詳情

*   **`readiness_verdict`** (`str`) - *判定該安裝或時段是否達標的最終結論*
    *   **可能值**：`"PASS"`, `"FAIL"`
    *   **判斷邏輯**：
        1.  若 `DNS` 為 `FAIL`，直接判定為 `"FAIL"`。
        2.  若為 **Wi-Fi** 設備，檢查下列門檻，任一不合格即為 `"FAIL"`：
            `Latency(P95) <= 60ms`, `Loss(P95) <= 1%`, `Retry(P95) <= 10%`, `PhyRate(P50) >= 100Mbps`。
        3.  若為 **Cable** 設備，檢查下列門檻，任一不合格即為 `"FAIL"`：
            `US_Latency(P95) <= 80ms`, `OFDM_MER(P5) >= 32dB`。
        4.  全數過關則為 `"PASS"`。

*   **`closure_readiness`** (`str`) - *決定工單是否允許被結案*
    *   **可能值**：`"ready"`, `"not_ready"`
    *   **判斷邏輯**：完全依賴 `readiness_verdict`。若其值為 `"PASS"` 則為 `"ready"`，否則為 `"not_ready"`。

*   **`dominant_factor`** (`str`) - *標示導致驗證失敗的最主要因子*
    *   **可能值**：`"WAN"`, `"WIFI"`, `"OPAQUE"`, `"UNKNOWN"`, 或特定 `ReasonCode` (如 `PLANT_IMPAIRMENT`)。
    *   **判斷邏輯**：若優先遇到 DNS FAIL，則寫入 `"WAN (DNS)"`；否則寫入陣列中**第一個** `ReasonCode` 經由字典翻譯後的結果。

*   **`confidence`** (`float`) - *系統對此次驗證結果的信心水準*
    *   **可能值**：`0.0` \~ `1.0` (如 `0.85`)
    *   **判斷邏輯**：若結論為 FAIL，基礎值給予 `0.8`；若為 PASS，基礎值給予 `0.85`。若分析樣本數 `>= 18` 筆，額外加成 `0.1` (最高不超過 `0.95`)。

---

## 🪪 3. 證據生成層 (ProofCard / PC-Min - `M13_fp_lite`)
當觸發 OBH (一鍵產出) 或要求出示證據包時，所形成的最終事實紀錄。

### 欄位詳情

*   **`status`** (`str`) - *ProofCard 本身的整備狀態與合規性*
    *   **可能值**：`"READY"`, `"NOT_READY"`, `"INSUFFICIENT_EVIDENCE"`
    *   **判斷邏輯**：
        1. 樣本數 `< MIN_SAMPLES` -> `"INSUFFICIENT_EVIDENCE"`
        2. 若 threshold 檢查有失敗的 `reasons` -> `"NOT_READY"`
        3. 無任何失敗項目 -> `"READY"`

*   **`diagnosis_code`** (`str`) - *該證據卡總結的異常根本原因分類*
    *   **可能值**：`"WAN_UNSTABLE"`, `"WIFI_CONGESTION"`, `"UNKNOWN"` 等
    *   **判斷邏輯**：基於 M13 傳回的首個錯誤代碼 (`reasons[0]`) 查表推導得出。

*   **`reason_code`** (`List[str]`) - *列出所有未達標的具體量測項目代碼*
    *   **可能值**：`["P95_RTT_TOO_HIGH"]`, `["PLANT_IMPAIRMENT_SUSPECT"]`, `["LOW_PHY_RATE"]`...
    *   **判斷邏輯**：由 Profiler 掃描每項 Threshold，紀錄所有突破門檻的代碼。

*   **`validity_grade`** (`str`) - *此證據卡可被採信的法律與合約位階*
    *   **可能值**：`"DELIVERY_GRADE"`, `"CLOSURE_GRADE"`, `"NOT_CLOSURE_GRADE"`
    *   **判斷邏輯**：若調閱情境 (`context`) 包含 `dispute` 或 `compliance`：且該報告若已簽署則得 `"CLOSURE_GRADE"`，否則退回 `"NOT_CLOSURE_GRADE"`。未指定情境時預設皆為 `"DELIVERY_GRADE"`。

*   **`health_checks`** (`List[CheckResult]`) - *詳細條列 Threshold 的過關/失敗細節*
    *   **可能值**：`[{name: "Latency", threshold: "<=60", actual: "45", status: "PASS", reason: null}]`
    *   **判斷邏輯**：直接輸出 `ProfileBase.check()` 的陣列結果。

*   **`outcome_facet`** (`List[Dict]`) - *呈現於 UI 面板上的關鍵指標數值摘要*
    *   **可能值**：`[{"name": "rtt_p95", "value": 45.2, "unit": "auto"}]`
    *   **判斷邏輯**：若狀態為 FAILED 時抽取 p95，否則抽取 p50 作為代表性數值。

*   **`missing_evidence_class`** (`List[str]`) - *記載缺少了什麼要件導致證據無法完整*
    *   **可能值**：空陣列 或 `["PRIVACY_POLICY_MISSING"]`
    *   **判斷邏輯**：在 M22 Base Validity Hook 中檢查 `attempt.observability.missing_refs` 判斷。

---

## 🛡️ 4. 隱私稽核層 (Privacy Governance / PC-Priv - `M22_privacy_governance`)
掌控權限、視野與資料脫敏的機密級管制。

### 欄位詳情

*   **`observability_status`** (`str`) - *標示此設備是否有足夠的底層權限可觀測問題*
    *   **可能值**：`"SUFFICIENT"`, `"INSUFFICIENT"`
    *   **判斷邏輯**：判斷 `missing_refs` 陣列是否為空，沒有遺失要件即為 `"SUFFICIENT"`。

*   **`opaque_risk`** (`bool`) - *判斷是否有黑箱設備阻擋探測*
    *   **可能值**：`True`, `False`
    *   **判斷邏輯**：若設備處於路由後方且不支援透通協議時為 `True`。

*   **`policy_valid`** (`bool`) - *附加在 refs 中的 flag，指示此卡是否合法合規*
    *   **可能值**：`True`, `False`
    *   **判斷邏輯**：若 `missing_refs` 中存在缺失 (如 PrivacyPolicyMissing) 導致 Base Validity Hook 不通過，則標示為 `False`。

*   **`egress_receipt_ref`** (`str`) - *獲准匯出 Sensitive Payload 才會派發的憑證收據*
    *   **可能值**：`"EGRESS-REC-a1b2c3d4..."`, 或 `None`
    *   **判斷邏輯**：當請求方的權限 (`authority`) 符合證據卡的揭露範圍 (`disclosure_scope`)，或使用 `admin_override` 時，才會核發 UUID 序號。若權限不符則強制為 `None`。

*   **`gate_ref`** (`str`) - *當前這份報告套用的 Egress (匯出) 守門規則版本*
    *   **可能值**：`"EG-STRICT-V2"`, `"EG-DEFAULT-V1"`
    *   **判斷邏輯**：若 M22 開啟 `strict_mode=True` 則套用 STRICT-V2，反之套用 DEFAULT-V1。

*   **`payload`** (`Dict` | `None`) - *完整的時間軸數據矩陣*
    *   **可能值**：`{...}` 或 `None`
    *   **判斷邏輯**：與 `egress_receipt_ref` 邏輯生死綁定。若權限不符，此機密欄位會被強制覆寫清空為 `None`，代表機密數據已被截斷，僅允許展示外層的 Metadata (PC-Min/PC-Priv)。

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
