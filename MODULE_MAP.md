
# Module Map (M1–M19)

| ID | File | Purpose |

|---:|---|---|
| M00 | M00_common.py | 共用定義 (Common) - 定義共用資料結構 (如 MetricSample, ChangeEventCard) 與通用工具函式。 |
| M01 | M01_windowing.py | 視窗管理 (Windowing) - 負責生成視窗參考 (Ws, Wl) 並協助緩衝區與事件捕獲的時間對齊。 |
| M02 | M02_ring_buffer.py | 環形緩衝區 (Ring Buffer) - 提供始終在線的滾動數據結構，用於儲存指標與事件。 |
| M03 | M03_metrics_collector.py | 指標收集器 (Metrics Collector) - 負責每 10 秒採樣一次指標數據。 |
| M04 | M04_change_event_logger.py | 變更事件記錄器 (Change Event Logger) - 捕獲命令/變更事件、生成版本參考，並記錄來源與觸發者。 |
| M05 | M05_snapshot_manager.py | 快照管理器 (Snapshot Manager) - 建立範圍化的變更前快照參考（僅參考，無回滾功能）。 |
| M06 | M06_observability_checker.py | 可觀察性檢查器 (Observability Checker) - 檢查最小參考是否存在，並在不足時標記不透明風險 (Opaque Risk)。 |
| M07 | M07_incident_detector.py | 事件檢測器 (Incident Detector) - 通過多信號檢測壞視窗 (Bad Window)。 |
| M08 | M08_verdict_classifier.py | 判決分類器 (Verdict Classifier) - 進行最小判決分類 (如 WAN, WiFi, Mesh, DFS 等)。 |
| M09 | M09_episode_manager.py | 事件管理器 (Episode Manager) - 負責追蹤事件 (Episode ID)、最壞視窗與證據參考。 |
| M10 | M10_timeline_builder.py | 時間軸建構器 (Timeline Builder) - 生成扁平化的事件時間軸 (指標 + 事件 + 快照)。 |
| M11 | M11_bundle_exporter.py | 證據包導出器 (Bundle Exporter) - 負責將數據導出為 JSON 格式的證據包。 |
| M12 | M12_obh_controller.py | OBH 控制器 (OBH Controller) - 協調凍結數據 (快照緩衝區) 與事件綁定，並執行導出。 |
| M13 | M13_fp_lite.py | fp-lite 計算 (fp-lite) - 計算 Before/During/After 狀態及 BOSD 標籤。 |
| M14 | M14_bundle_reader.py | 證據包讀取器 (Bundle Reader) - 負責加載與讀取證據包。 |
| M15 | M15_cli_offline_fp.py | 離線 fp-lite CLI 工具 - 提供離線分析用的命令行工具。 |
| M16 | M16_recognition_engine.py | 識別引擎 (Recognition Engine) - 綜合事件追蹤、風險標記與事件綁定，生成識別結果。 |
| M17 | M17_demo_simulator.py | 演示模擬器 (Demo Simulator) - 提供無硬體的演示運行環境。 |
| M18 | M18_app_integration_notes.md | 應用集成指南 (Integration Guide) - 提供離線/應用執行模型的集成文檔。 |
| M19 | M19_schema_appendix.md | Schema 附錄 (Schema Appendix) - 提供 JSON Schemas 與附錄說明 (對應 SCHEMA_APPENDIX.md)。 |
| M20 | M20_install_verify.py | 安裝驗證 (Install Verify) - 負責執行安裝後的驗證邏輯 (預設 3 分鐘)，產出 Pass/Marginal/Fail 判決。 |
| Core | core_service.py | 核心服務 (Core Service) - 負責協調數據採樣、緩衝區更新與事件迴圈的核心服務 (OBHCoreService)。 |
| Server | server.py | 演示伺服器 (Demo Server) - 基於 FastAPI 的 REST 伺服器，提供 Dashboard API 與模擬觸發介面。 |
