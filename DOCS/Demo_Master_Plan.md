# DAE_P1 隱私治理：Master Demo 展示大綱

本計畫結合「隱私放射科」的感性隱喻與「出口守門人」的理性驗證，打造一個耳目一新的報告體驗。

---

## 階段一：感性開場 —— 數據的「解析度」 (The Radiology Metaphor)
**目的：** 用一公里的高度建立共識，強調隱私是動態的，而非傳統的開關。

*   **口頭開場：** 「在過去，資料庫存取就像給這把鑰匙（開或關）。但 DAE P1 引入了『數據解析度』的概念。就像放射科醫生：平時看 X 光（診斷），必要時看 MRI（調解）。」
*   **視覺展示 (UI)：**
    - 展示一個**普通客服場景**。
    - 指著螢幕說：「現在解析度只有 10%。我們能看到診斷結論 (`verdict`)，但具體的數據 (`payload`) 是模糊的。這是系統為了保護用戶，主動『剝離』了細節。」
*   **關鍵操作：** 指向 `PC-Min` 標籤頁。

---

## 階段二：理性驗證 —— 守門人的「邏輯閘」 (The Egress Gate Verification)
**目的：** 轉向「專家模式」，現場展示後台如何根據欄位選項即時執行邏輯。

### 場景 1：身分與權限的碰撞 (Hook 2)
*   **操作：**
    1.  將 `authority_scope_ref` 從 `EMPTY` 改為 `isp-support`。
    2.  觀察：Hook 2 燈號亮綠。
*   **敘事：** 「系統識別了你的行政職權。你看，出口閘門檢測到你是合規的維修工程群組。」

### 場景 2：意圖 (Context) 的決定性 (Hook 3)
*   **操作：**
    1.  切換 `byuse_context_ref` 為 `routine` (常規)。
    2.  展示：`evidence_grade` 為 `DELIVERY`。
    3.  **關鍵點：** 打開 Payload 欄位，發現是 `NULL`。
*   **敘事：** 「雖然身分對了，但意圖不符。在『常規維護』下，系統依然拒絕提供敏感數據。這就是我們的主動保護機制。」

### 場景 3：終極「解凍」路徑 (Signed Dispute)
*   **操作：**
    1.  將 `byuse_context_ref` 改為 `dispute` (爭議)。
    2.  將 `is_signed` 勾選為 `True`。
    3.  即時觀察：`evidence_grade` 跳轉為 `CLOSURE`。
    4.  展示：`PC-Priv` 標籤頁出現數據，`egress_receipt_ref` 自動生成序號。
*   **敘事：** 「只有當『身分 + 爭議意圖 + 證據簽章』三者齊備時，數據才會解凍。並且，系統會留下一個不可抹滅的出口收據（Egress Receipt）。」

---

## 三、Demo 數據對照矩陣 (Cheat Sheet)

| 展示階段 | `authority_scope_ref` | `context_ref` | `is_signed` | 預設輸出 | 關鍵訊息 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **開場** | `isp-support` | `routine` | `False` | **PC-Min** | 隱私優於便利 (Default Privacy) |
| **技術驗證** | `isp-support` | `dispute` | `False` | **NOT_CLOSURE** | 證據不可結案，數據仍被剝離 |
| **最終達成** | `isp-support` | `dispute` | `True` | **PC-Priv** | 證據閉環，解鎖完整解析度 |

---

## 四、結語：金句摘要 (Conclusion)
> 「這不僅僅是一個診斷工具，它是一個自我約束的隱私系統。數據不再是一個靜態資產，而是一個受控的資料流，流動的權限由系統內建的三個 Hook 即時決定。」
