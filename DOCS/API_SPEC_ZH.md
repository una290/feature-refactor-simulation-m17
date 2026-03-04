# DAE P1 後端 API 規格書 (內部開發版)

本文件詳細說明了目前 `server.py` 實作中所有可用的 REST API 端點。此版本專為內部開發與對接快速參考而設。

---

## 🛑 開發與對接注意事項 (重要)

在開始串接任何端點前，請先注意以下目前的實作預設：

1. **認證與授權 (Auth)**：
   - 目前處於「Demo / Free V1」階段，**沒有實施 Token 或 Cookie 驗證機制**。
   - 但資料**降級與隱私權限**是透過查詢參數 `authority_scope_ref` (存取權限範圍，例：`isp-support`) 與 `byuse_context_ref` (使用情境，例：`dispute`) 來模擬控制。
2. **CORS 設定**：
   - 已全面開放 `allow_origins=["*"]`，前端本機開發 (例如 `localhost:3000`) 不會遇到 CORS 問題。
3. **錯誤處理 (Error Handling)**：
   - 伺服器不會拋出傳統的 4xx/5xx HTTP 錯誤碼 (除了嚴重當機)。
   - 預期外的狀況會一律回傳 HTTP 200，但 JSON 內容會帶有 `error` 或 `message` 鍵值，例如：`{"error": "Episode not found."}`。前端必須自行檢查這個欄位。

---

## 1. 核心與指標 API (Core & Metrics APIs)

### 1.1 GET /
- **說明**：伺服器啟動狀態檢查。
- **輸出**：`{"status": "running", "service": "DAE_P1 Demo Core V1.3"}`

### 1.2 GET /metrics
- **說明**：取得 Ring Buffer 中最新一筆指標樣本。
- **輸出預期型態**：`MetricSample` 物件 JSON (若無資料則為 `{"message": "No metrics collected yet"}`)。

### 1.3 GET /metrics/history
- **說明**：取得最近的指標歷史資料。
- **參數**：`limit` (整數, 預設: 20) -> 限制回傳筆數。
- **輸出**：陣列 `[MetricSample, ...]`

### 1.4 GET /events
- **說明**：取得近期網路或系統變更事件。
- **輸出**：陣列 `[ChangeEventCard, ...]`

### 1.5 GET /snapshots
- **說明**：取得變更前記錄的系統快照。
- **輸出**：陣列 `[PreChangeSnapshot, ...]`

### 1.6 GET /recognition
- **說明**：觸發 M16 負責判定目前的「網路事件判決」(例如: 是否塞車)。
- **輸出**：
  ```json
  {
    "episode_id": "ep-xxxx",
    "primary_verdict": "WIFI_CONGESTION",  // 判定結果
    "confidence": 0.95,
    "evidence_refs": ["S-100", "E-200"],
    "observability": { "observability_status": "SUFFICIENT", "opaque_risk": false }
  }
  ```

### 1.7 GET /install_verify
- **說明**：觸發 M20 驗證裝機品質是否達標 (Closure Readiness)。
- **輸出**：
  ```json
  {
    "timestamp": 1718000000.0,
    "closure_readiness": "ready",  // or "not_ready"
    "readiness_verdict": "PASS",
    "dominant_factor": "PASSED_INSTALL"
  }
  ```

### 1.8 GET /status
- **說明**：取得本地設備的高階健康狀態。
- **輸出**：`{"status": "ok"}` (可能值: `ok`, `unstable`, `suspected`, `investigation`)

### 1.9 GET /modules
- **說明**：取得全部 19 個模組目前的啟動與資料負載狀態。
- **輸出**：陣列 `[{"id": "M01", "name": "Windowing", "status": "Active", "data": {}}, ...]`

---

## 2. 模擬與網路 API (Simulation & Network APIs)

### 2.1 GET /fleet
- **說明**：回傳雲端戰情室用的「假艦隊」檢視 (包含 1 台真實數據 + 2 台假數據)。
- **輸出**：陣列 `[{"id": "local", "current_state": "ok", ...}, ...]`

### 2.2 GET /device/{device_id}
- **說明**：取得單一設備的詳細檢查清單與時間軸 (用於 CSR 儀表板深查)。
- **路徑參數**：`device_id` (通常帶入 `"local"`)

### 2.3 GET /api/wan & GET /api/lan
- **說明**：取得模擬的 WAN/LAN IP 與連線設備清單 (僅供 UI 展示用)。

### 2.4 POST /simulate/incident
- **說明**：人為注入網路異常以觸發系統偵測。
- **參數** (`query string`)：
  - `type` (預設 `"latency"`): 可選 `"retry"`, `"airtime"`, `"complex"`, `"stable"`, `"oscillating"`, `"degrading"`
  - `duration` (預設 30): 維持秒數。
- **輸出**：`{"status": "Simulating", "type": "latency", ...}`

---

## 3. OBH 協助與隱私授權 API (OBH & Privacy APIs)

### 3.1 POST /obh/trigger
- **說明**：由使用者端 (User App) 主動觸發，打包目前狀況並產出一組 `episode_id`。預設為不暴露隱私資料 (`PC-Min`) 的導出。
- **參數** (`query string`): `context` (選擇性, e.g., `routine`)
- **輸出**：`{"status": "Exported", "episode_id": "ep-xxxxxx", ...}`

### 3.2 GET /obh/proofcard/{episode_id}
- **說明**：CSR 讀取特定的 `episode_id` 報告。**這是決定前端能否看到私密資料 (`PC-Priv`) 的關鍵 API**。
- **參數** (`query string`): 
  - `context` -> 會強烈影響回傳的資料多寡！(例如帶入 `context=dispute`)
  - `fields` -> (新增) 帶入 `fields=pc_min` 可強制後端在序列化前拋棄巨大的 payload 陣列，達成毫秒級的高速回傳，專供歷史列表的極簡視圖使用。
- **輸出**：
  ```json
  {
    "status": "Retrieved",
    "episode_id": "ep-xxxx",
    "bundle": {
      "evidence_grade": "CLOSURE_GRADE", 
      "pc_min": { "verdict": "WIFI_CONGESTION", ... },
      "pc_priv": { "timeline": {...} }  // 如果 user 未授權或 context 不符，此欄位為 null !
    }
  }
  ```

### 3.3 POST /api/obh/consent/request
- **說明**：CSR 點擊「請求授權」時呼叫，通知系統該 `episode_id` 正在等待使用者點頭。
- **Body**：`{"episode_id": "ep-xxxx", "csr_id": "csr-1234"}`

### 3.4 GET /api/obh/consent/pending
- **說明**：User App 輪詢此 API，檢查畫面上是不是要彈出「CSR 正在請求授權」的視窗。(請求 15 分鐘後自動過期失效)。
- **輸出**：`{"pending_requests": [{"episode_id": "ep-xxxx", "csr_id": "csr-1234", "timestamp": ...}]}`

### 3.5 POST /obh/manifest/sign
- **說明**：User 在 App 點擊「同意」時呼叫，將該 `episode_id` 加入白名單，解鎖給 CSR 觀看 `PC-Priv`。
- **Body**：`{"episode_id": "ep-xxxx"}`

### 3.6 GET /obh/history_summary
- **說明**：(新增) 取得系統中所有已保存的 Proof Card 的輕量化歷史紀錄清單，陣列依時間由新到舊排序。
- **輸出**：
  ```json
  {
    "status": "Success",
    "history": [
      {
        "episode_id": "ep-xxxx",
        "profile_ref": "WIFI78_INSTALL_ACCEPT",
        "window_ref": "W-LATEST-100",
        "verdict": "FAIL",
        "time": "2023-10-27T10:00:00Z",
        "is_dispute": true,
        "is_signed": false
      }
    ]
  }
  ```

---

## 4. V1.3 示範功能 API ✨ (V1.3 Specific APIs)

### 4.1 GET /device/{device_id}/proof
- **說明**：根據給定的條件 (Profile) 動態生出一張全新的 V1.3 證明卡 (ProofCard)。
- **路徑參數**：`device_id` (帶入 `"local"`)
- **參數** (`query string`)：`profile` (預設 `"WIFI78_INSTALL_ACCEPT"`)
- **輸出**：直接回傳完整的 `ProofCard` JSON，包含 Payload 與判定細節 (`health_checks`)。

### 4.2 GET /device/{device_id}/manifest
- **說明**：取得可用資料清單 (Data Manifest)。這就像是問資料庫「你有幾天的資料？有發生過幾種事件？」。
- **輸出**：`{"manifest_ref": "man-xxx", "available_day_refs": [...], "available_event_refs": [...]}`
