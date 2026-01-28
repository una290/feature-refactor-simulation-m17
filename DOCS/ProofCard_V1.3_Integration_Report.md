# DAE ProofCard V1.3 整合報告

本文件統整了將「DAE ProofCard Free on CPE — 工程規格書 V1.3」整合至系統中的所有變更與實作細節。

## 1. 核心基礎架構更新 (Core Infrastructure)

為符合規格書對於「本地保存」與「索引真實性」的要求，我們對核心服務進行了以下升級：

| 項目 | 檔案 | 變更說明 | 目的 |
| :--- | :--- | :--- | :--- |
| **資料保存期限** | `server.py` | 將 Ring Buffer 大小從 **60 分鐘** 延長至 **7 天 (10080 分鐘)**。 | 符合規格書「2.2 本地保存」要求，確保消費爭議發生時有足夠的歷史數據。 |
| **Manifest 索引** | `M21_manifest_manager.py` | 從 Mock 模式改為 **實作 SQLite 查詢**。直接查詢資料庫 (`metrics.db`) 中實際存在的日期。 | 符合「P4 可調取」原則，Manifest 索引必須反映真實資料範圍。 |
| **有效性檢查** | `M13_fp_lite.py` | 新增 `validity_verdict` 判斷邏輯：<br>1. 超過 24 小時 ➔ `STALE`<br>2. 超過 7 天 ➔ `OUT_OF_SCOPE` | 確保 ProofCard 產出時會標註數據的時效性狀態。 |
| **統計修正** | `M13_fp_lite.py` | 修正欄位對應 (Mapping) 與空值處理，解決 `p50`/`p95` 統計為 0 的 Bug。 | 確保生成的統計數據正確且可對帳。 |

## 2. 規範 Sections 4-7 實作 (Manifest & Profiles)

針對規格書中定義的 Profile、事件類型與索引機制進行的實作：

### 2.1 常數與標準化 (M00, M07)
*   **標準化代碼 (M00)**: 新增 `EventType` (如 `MLO_LINK_FLAP`, `RTT_SPIKE_TAIL`) 與 `ReasonCode` (如 `P95_RTT_TOO_HIGH`)。
*   **事故偵測 (M07)**: 將偵測結果的輸出從自訂字串統一為上述標準代碼。

### 2.2 Manifest 事件索引優化 (Section 4)
*   **實作細節**: `server.py` 將 Event Buffer 傳遞給 `M21`，使其能查詢 SQLite 中的 `events` 表。
*   **成果**: `/device/local/manifest` 現在會列出 `available_event_refs`，顯示由系統偵測並保存的實際事件清單。

### 2.3 領域 Profile 擴充 (Section 7)
實作了完整的 Wi-Fi 7/8 與 FWA Profile 檢查邏輯 (M13)：

| 領域 | Profile Ref | 檢查重點 (Outcome Facets) |
| :--- | :--- | :--- |
| **Wi-Fi 7/8** | `WIFI78_INSTALL_ACCEPT` | p95 RTT, p95 Loss, Phy Rate |
| | `WIFI78_MESH_BACKHAUL_SPLIT` | Backhaul RSSI (p5), MLO Link Switch |
| | `WIFI78_OSCILLATION_GUARD` | Retry Rate (p95) |
| **FWA** | `FWA_INSTALL_ACCEPT` | RSRP (p5), SINR (p5) |
| | `FWA_PLACEMENT_GUIDE` | 方向性指引 (RSRP/Signal) |
| | `FWA_CONGESTION_SUSPECT` | 晚高峰擁塞偵測 (Tail RTT) |

## 3. Cable Modem (DOCSIS) 支援擴充

為支援 Cable Modem (DOCSIS) 設備診斷，擴充了資料結構與檢查邏輯 (Section 7.3)：

### 3.1 資料結構擴充 (M00)
新增 `MetricSample` 欄位以支援 DOCSIS 特定指標：
*   **穩定性指標**: `t3_count`, `t4_count` (Ranging Timeout)。
*   **訊號品質**: `ofdm_mer_db` (MER), `fec_corrected`, `fec_uncorrected`。
*   **延遲**: `us_latency_p95_ms` (上行延遲，針對 Bufferbloat)。

### 3.2 Cable 專用 Profile (M13)
新增三組專用 Profile：

1.  **`CABLE_INSTALL_ACCEPT`**
    *   **用途**: 標準安裝驗收。
    *   **檢查**: 上行延遲 (p95) 是否過高、MER (p5) 是否達標。
2.  **`CABLE_UPSTREAM_INTERMITTENT`**
    *   **用途**: 抓取間歇性斷線問題。
    *   **檢查**: T3/T4 逾時次數爆發 (`T3T4_RETRY_BURST`)。
3.  **`CABLE_PLANT_IMPAIRMENT_SUSPECT`**
    *   **用途**: 判斷是否為外部線路 (Plant) 問題。
    *   **檢查**: MER 驟降、FEC 錯誤爆發。

---
**文件生成時間**: 2026-01-27
**版本**: DAE P1 V1.3 Integration
