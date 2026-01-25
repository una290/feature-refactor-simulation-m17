# DAE P1 系統參數列表

本文件列出了 DAE P1 程式碼庫中所有 **自定義、預設和硬編碼的參數**。

## 1. 可配置參數 (Runtime Config)

這些參數定義在 dataclasses 中，並且可以在初始化時被覆寫。

### Window Policy (視窗策略)
**檔案**: `dae_p1/M01_windowing.py` (類別: `WindowPolicy`)
- `ws_sec`: **10**
  - **描述**: 短視窗生成間隔（秒）。用於標籤 (labeling)。
- `wl_sec`: **60**
  - **描述**: 長視窗生成間隔（秒）。用於標籤 (labeling)。

### Core Service Configuration (核心服務配置)
**檔案**: `dae_p1/core_service.py` (類別: `CoreRuntimeConfig`)
- `sample_interval_sec`: **10**
  - **描述**: 指標收集的間隔時間（秒）。
- `buffer_minutes`: **60**
  - **描述**: 將指標保留在滾動環形緩衝區中的持續時間（分鐘）。
- `accelerate`: **False**
  - **描述**: 如果為 True，則忽略 `sleep()` 以進行快速演示執行。

---

## 2. BDB Proof V2 Policy (主要邏輯)

**檔案**: `dae_p1/vendors/bdb_proof/configs/default_policy.yaml`

識別引擎 (M16) 使用此外部 YAML 策略進行所有事件檢測和准入邏輯。

### BDB Windowing (視窗化)
- `window_seconds`: **300** (5 分鐘) (位於 `M16_recognition_engine.py`)
- `cooldown_seconds`: **600** (10 分鐘) (Counterforce 冷卻時間)

### FP Lite Thresholds (FP Lite 閾值)
定義在策略的 `fp_lite` 部分：

| 指標 | 等級 (低 / 中 / 高) |
|--------|---------------------------|
| WAN RTT (ms) | 80 / 150 / 250 |
| WAN Loss (%) | 1 / 2 / 5 |
| Retry Rate (重試率) | 0.05 / 0.15 / 0.25 |
| Airtime Busy (通話時間佔用) | 0.60 / 0.75 / 0.90 |
| Steer Count (引導次數) | 5 / 12 / 20 |
| Temp (攝氏度) | 70 / 85 / 92 |

### BDB Boundaries (觸發邊界)
- **Steering Oscillation (引導振盪)**: 引導次數 (Steer count) > **12**
- **WAN Tail (WAN 尾部延遲)**: RTT > **150**ms 或 Loss > **2**%
- **Thermal (熱過載)**: 溫度 (Temp) > **88**C

---

## 3. Installation Verification (M20 安裝驗證)

**檔案**: `dae_p1/M20_install_verify.py`

由 `install_verify_run.py` 和 `server.py` 用於特定的驗證流程。

| 參數 | 數值 | 邏輯 |
|-----------|-------|-------|
| `DEFAULT_VERIFY_WINDOW_SEC` | **180** (3分鐘) | 驗證分析的預設期間。 |
| **PASS** 標準 | | |
| Loss Limit (掉包限制) | ≤ **1.0**% | |
| Latency Limit (延遲限制) | ≤ **60.0**ms | |
| Retry Limit (重試限制) | ≤ **12.0**% | |
| Mesh Flap Limit (Mesh 翻動限制) | < **2** | |
| **FAIL** 標準 | | |
| Loss Limit (掉包限制) | > **3.0**% | |
| Latency Limit (延遲限制) | > **120.0**ms | |
| Retry Limit (重試限制) | > **25.0**% | |
| Mesh Flap Limit (Mesh 翻動限制) | ≥ **3** | |

---

## 4. Other Constants (其他常數)

### Observability Checks (可觀測性檢查)
**檔案**: `dae_p1/M06_observability_checker.py`
- `MIN_REFS`: `["origin_hint", "change_ref", "version_refs"]`
  - **描述**: 標記可觀測性為 `SUFFICIENT` 所需的欄位。

### Buffer Sizes (緩衝區大小)
**檔案**: `dae_p1/core_service.py`
- `events_buf` size: **500** items
- `snaps_buf` size: **500** items
- `metrics_buf` size: 推導值 (~360 items @ 10s interval for 60m)

**檔案**: `dae_p1/M00_common.py`
- `VersionRefs.agent`: **"dae_p1/0.1.0"**
- `Verdict` 類型: `WAN_UNSTABLE`, `WIFI_CONGESTION`, `MESH_FLAP`, `DFS_EVENT`, `OPAQUE_RISK`, `UNKNOWN`
