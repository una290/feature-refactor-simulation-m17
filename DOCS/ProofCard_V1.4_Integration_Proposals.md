# BREL 隱私規範併入 V1.3 的三種提案 (Proposals)

根據 BREL 文件，我們有幾種不同的方式將 Privacy Hooks 融入原有的 V1.3 規格中。以下提供三個不同架構深度的提案：

## 提案 A：嚴格疊加法 (Strict Overlay / Minimal Code Impact)
**做法：** 保持 V1.3 核心欄位與邏輯完全不動，將 BREL 定義的所有 Privacy 欄位包裝成一個額外的 `BREL_Extension` 欄位（例如在 JSON 中增加一個 `extensions.privacy` 物件）。
- **優點：** 最小化對現有系統 (`M13_fp_lite.py` 與前端 UI) 的修改幅度。舊系統不需要理會這塊也能正常解析原有的 ProofCard。
- **缺點：** 未真正落實 BREL 文件的「隱私作為有效性前提 (Privacy Precondition)」精神，隱私門控變成一個選配模組，可能引發稽核爭議。

## 提案 B：深度融合法 (Deep Integration) —— **推薦與已實作的 V1.4 版本**
**做法：** 直接重構 ProofCard 資料結構，徹底拆分為 `PC-Min` 與 `PC-Priv` 兩大平行區塊。將 Privacy Check 放進系統核心 Admission 判定流程中。並在輸出端強制掛上 Egress Gate。
- **優點：** 完美契合 BREL 文件的「One Spine」架構與「四海皆準」精神。從根本上解決不同網域與設備外送資料時的隱私外洩風險。
- **缺點：** 需要對原有的 ProofCard 定義類別 (位於 `M00_common.py`) 以及生成邏輯 (`M13_fp_lite.py`) 進行較大幅度的重構，以支援雙層資料與 Egress 回執。

## 提案 C：Profile 擴充法 (Profile-Based Extension)
**做法：** 將 BREL 隱私功能綁定在特定的 `profile_ref` 端。只有當呼叫的 Profile 屬於高敏感領域 (例如 `PROFILE_OPENRAN_RIC` 或新增的 `WIFI78_SECURE_ACCEPT`) 時，才強制啟用 PC-Min/Priv 雙層結構與 Egress Gate；否則退回標準 V1.3 結構。
- **優點：** 彈性最高，對一般的 CPE 基本連線診斷維持最低計算與資料負擔。
- **缺點：** 導致系統在不同 Policy 下，ProofCard 的結構 (`dataclass`) 與匯出邏輯不一致，維護成本較高。

---
**目前進度與建議：** 考量到 BREL 文件的設計初衷是「建立無法繞過的承認條件」，我們強烈建議採用 **提案 B**。目前也已經為您基於提案 B 撰寫了 `ProofCard_Free_V1.4_Spec.md` 規格書草案。如果符合預期，我們就可以根據此版本開始修改 Python 程式碼 (`M00`, `M13` 等)。如果您傾向提案 A 或 C，我們也能重新調整規格書與實作方向。
