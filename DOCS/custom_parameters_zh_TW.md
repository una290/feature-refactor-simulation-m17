# DAE P1 系統參數列表

本文件列出了 DAE P1 程式碼庫中前端與後端所有 **自定義、預設和硬編碼的參數**。
(基於 Codebase: `DAE_P1_19Modules-feature-refactor-simulation-m17`)

## 1. 系統連線配置 (System Connection)

### 前端 App (Frontend)
**檔案**: `dae-mobile-app/src/api.js`
- `API_BASE_URL`: **'http://172.18.129.27:8000'**
  - **描述**: App 連線至後端 Server 的 IP 位址。
  - **注意**: 部署或更換網路環境時，必須修改此 IP 為執行 Server 的電腦 IP。

### 後端 Server (Backend)
**檔案**: `server.py`
- `HOST`: **"0.0.0.0"**
  - **描述**: 監聽所有網路介面，允許外部裝置連線。
- `PORT`: **8000**
  - **描述**: Backend API 服務埠號。

---

## 2. 核心服務配置 (Core Service Runtime)

**檔案**: `dae_p1/core_service.py` (定義) & `server.py` (執行實例)

這些參數定義了數據收集與處理的頻率及保存策略。

| 參數 | 程式碼預設值 | 此專案 Demo 設定 (`server.py`) | 描述 |
|------|------------|---------------------------|------|
| `sample_interval_sec` | 10 | **1** | 指標收集的間隔時間（秒）。Demo 為了即時性加速為 1秒。 |
| `accelerate` | False | **True** | 是否忽略 `sleep()` 進行快速演示。 |
| `buffer_minutes` | 60 | **10080** (7天) | 指標保留在記憶體/DB中的時間範圍（分鐘）。V1.3 要求 7 天。 |
| `persistence_enabled` | True | **True** | 是否將數據寫入 SQLite 資料庫。 |
| `db_path` | "data/cpe_metrics.db" | (預設) | SQLite 資料庫檔案路徑。 |

### Window Policy (視窗策略 - M01)
**檔案**: `dae_p1/M01_windowing.py` (類別: `WindowPolicy`)
- `ws_sec`: **10**
  - **描述**: 短視窗生成間隔（秒）。用於標籤 (labeling)。
- `wl_sec`: **60**
  - **描述**: 長視窗生成間隔（秒）。用於標籤 (labeling)。

---

## 3. 偵測邏輯與閾值 (Detection Logic & Thresholds)

本系統包含多層偵測邏輯，各自有獨立的閾值設定。

### A. M07 Incident Detector (基礎事件偵測)
**檔案**: `dae_p1/M07_incident_detector.py`
用於基本的訊號偵測（非 BDB 引擎）：

| 參數 | 閾值 | 觸發事件 |
|------|------|----------|
| `airtime_busy_pct` | >= **75.0**% | `OBSS_INTERFERENCE_SPIKE` |
| `retry_pct` | >= **18.0**% | `WIFI_SIDE_OSCILLATION` |
| `latency_p95_ms` | >= **60.0**ms | `RTT_SPIKE_TAIL` |
| `mesh_flap_per_min` | >= **2** | `MESH_BACKHAUL_WEAK` |
| `wan_sinr_low_db` | <= **5.0** dB | `LOW_SINR_P5` |

### B. M16 BDB Proof V2 Policy (進階識別引擎)
**檔案**: `dae_p1/vendors/bdb_proof/configs/default_policy.yaml` (策略)
**檔案**: `dae_p1/vendors/bdb_proof/core/windowing.py` (視窗)

* `window_seconds`: **300** (5分鐘) - BDB 分析視窗
* `cooldown_seconds`: **600** (10分鐘) - 事件冷卻時間

**BDB 觸發邊界**:
- **Steering Oscillation**: 引導次數 > **12**
- **WAN Tail**: RTT > **150**ms 或 Loss > **2**%
- **Thermal**: 溫度 > **88**C

### C. M13 FP Lite Profiles (Proof Card 生成規則)
**檔案**: `dae_p1/M13_fp_lite.py` (`ProfileBase` 子類別)
這些閾值用於生成 V1.3 Proof Card。

**Wi-Fi 7/8 (Install Accept)**:
- RTT P95 > **60.0** ms (Warning)
- Loss P95 > **1.0** % (Warning)
- Retry P95 > **10.0** % (Warning)
- Phy Rate P50 < **100** Mbps (Low Speed)

**FWA (Install Accept)**:
- RSRP P5 < **-110** dBm (Weak Coverage)
- SINR P5 < **0** dB (Low SINR)

**Cable (Install Accept)**:
- Upstream RTT P95 > **80.0** ms
- OFDM MER P5 < **32.0** dB

**Cable (Upstream Intermittent)**:
- T3 Count P95 > **5**
- Upstream RTT P95 > **150.0** ms

---

## 4. Installation Verification (M20 安裝驗證)

**檔案**: `dae_p1/M20_install_verify.py`
專用於 App 端「安裝驗證」功能的即時檢測。

- `DEFAULT_VERIFY_WINDOW_SEC`: **180** (3分鐘)

**PASS 判定標準 (嚴格)**:
只有當所有指標都**低於或等於**下列值時才為 PASS：

| 檢查項目 | PASS 上限 | FAIL 觸發 |
|----------|-----------|-----------|
| `wan_sinr_db` | >= **5.0** | < 5.0 |
| `airtime_busy_pct` | <= **75.0**% | > 75.0% |
| `retry_pct` | <= **12.0**% | > 12.0% |
| `signal_strength_pct`| >= **80**% | < 80% |
| `mesh_flap_count` | < **2** | >= 2 |
| `loss_pct` (Opaque) | <= **1.0**% | > 1.0% |
| `latency_p95_ms` | <= **60.0**ms | > 60.0ms |

---

## 5. Demo Simulation Constants (模擬器參數)

**檔案**: `dae_p1/M17_demo_simulator.py`
當系統在非 Windows 環境或 Demo 模式下運行時，這些數值控制模擬數據的行為。

**基本參數 (Stable Scenario)**:
- `retry_base`: **0.06** (6%)
- `airtime_base`: **0.35** (35%)
- `rssi_mean`: **-55.0** dBm

**故障模擬參數**:
- **Oscillating (震盪)**:
  - Retry: **22%** ~ **30%** (交互跳動)
  - Airtime: **55%** ~ **78%**
- **Degrading (持續惡化)**:
  - Retry: 隨時間增加至 **35%+**
  - RTT: 隨時間增加至 **200ms+**

---

## 6. Data Schema & Limits (資料結構與限制)

**檔案**: `dae_p1/core_service.py`
- `events_buf`: **500** items
- `snaps_buf`: **500** items
- `metrics_buf`: 依據 7 天保存期約 **60萬筆**。

**檔案**: `dae_p1/M06_observability_checker.py`
- `MIN_REFS`: `["origin_hint", "change_ref", "version_refs"]` (必填欄位)

**檔案**: `dae_p1/M00_common.py` (MetricSample)
**支援指標欄位**:
- **Wi-Fi**: `latency_p95_ms`, `loss_pct`, `retry_pct`, `airtime_busy_pct`, `signal_strength_pct`, `phy_rate_mbps`
- **WAN/FWA**: `wan_sinr_db`, `wan_rsrp_dbm`
- **Cable**: `t3_count`, `t4_count`, `us_latency_p95_ms`, `us_loss_pct`, `ofdm_mer_db`, `fec_corrected`
