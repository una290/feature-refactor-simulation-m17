# DAE 19 Modules 核心文件索引 (Document Index)

此資料夾為專案的集中文件庫，為了保持整潔，我們將不必要的文件封存到了 `archive/`。
以下是現行主力文件的導覽指引，方便新接手的工程師快速尋找資源：

## 🚀 專案展示與整合 (Demo & Integration)
* **`Demo_Master_Plan.md`**：專案功能展示的總劇本與流程表。
* **`Cable_Integration_Guide.docx`**：DOCSIS Cable 架構的整合與 API 欄位對照說明書。
* **`ProofCard_V1.4_Integration_Proposals.md`**：關於 V1.4 證據卡 (ProofCard) 前後端整合的規劃提案。

## 📜 API 規格與資料結構 (API Specs)
* **`API_SPEC_ZH.md`** / **`.docx`**：前端 Mobile App 與後端 Server.py 溝通的最新繁體中文 API 介面定義。
* **`custom_parameters_zh_TW.md`** / **`.docx`**：系統支援的各種客製化參數與屬性字典說明。
* **`module_interfaces.md`**：系統內部 19 個模組之間的輸入輸出定義（Developer Reference）。

## ⚙️ 系統邏輯與架構 (Architecture & Logic)
* **`system_workflow.md`**：從資料搜集、模組判斷到生成報告的整體系統運作流程圖與說明。
* **`Privacy_Logic_V2.md`**：升級後的隱私與權限稽核邏輯說明 (PC-Min vs PC-Priv)。
* **`MODULE_MAP.md`** & **`CAPABILITY_MAP.md`**：19 模組的功能地圖與系統能力矩陣，適合快速俯瞰專案 Scope。

## 📂 子資料夾 (Sub-directories)
* **`developer/`**：存放給韌體端、後端開發者的細部實作筆記與 Schema 定義 (例: `SCHEMA_APPENDIX.md`, `M19_readme.md` 等)。
* **`archive/`**：存放 V1.3 舊版文件、早期的測試報告與草稿，僅供歷史追溯使用。

> **註**：專案根目錄下的 `README.md` 保留為開發環境快速啟動與專案基底介紹。
