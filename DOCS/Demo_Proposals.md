# Demo 創新提案：解構「One Spine」隱私核心思想

這份報告拋棄傳統的條列式說明，改以**場景敘事**與**視覺隱喻**來展示隱私治理的核心重點。

---

## 核心選項與欄位對照表 (Demo 預備知識)

在開始提案前，先釐清系統中的核心欄位與可供 demo 的選項：

| 欄位名稱 (Field) | Demo 可選參數 (Options) | 核心意義 |
| :--- | :--- | :--- |
| **`authority_scope_ref`** | `isp-support`, `admin_override` | **「你是誰？」**(出口門檻) |
| **`byuse_context_ref`** | `routine` (常規), `dispute` (爭議) | **「你要做什麼？」**(使用意圖) |
| **`is_signed`** | `True`, `False` | **「證據是否有效？」**(數據完整性) |
| **`evidence_grade`** | `DELIVERY`, `CLOSURE`, `NOT_CLOSURE` | **「最終交付等級」**(輸出結果) |

---

## 提案一：【隱私放射科：數據解析度展示】(Analogy: Triage & Resolution)

**核心思想：** 隱私治理不是「給或不給」，而是「解析度」的調節。

*   **Demo 方式：**
    1.  **第一階段 (模糊觀測/PC-Min)：** 模擬普通客服進場。`scope=isp-support`, `context=routine`。螢幕上只顯示結論 (Verdict)。我們稱之為「隱私 X 光」，只能看到骨架。
    2.  **第二階段 (數據顯影/PC-Priv)：** 模擬爭議調解員。當切換 `context=dispute`。這時展示系統如何自動生成 `Egress Receipt` (出口收據)。
    3.  **第三階段 (法律閉環/Closure Grade)：** 點擊「數位簽章」。當 `is_signed=True` 時，`evidence_grade` 從 `NOT_CLOSURE` 躍升為 `CLOSURE`。就像這張 X 光片被醫生簽署，具備了法律效力。

---

## 提案二：【數據出口的守門人：即時邏輯矩陣】(Logic Matrix & Live Audit)

**核心思想：** 重點在於「為什麼數據被剝離？」。展示隱私治理是一個透明的「出口閘門」。

*   **Demo 方式：**
    1.  **左側輸入區：** 即時調整下拉選單 (`Routine` -> `Dispute`)。
    2.  **中央閘門區：** 動態顯示三個 Hook 的狀態燈。
        - 燈一：Hook 1 (數據完整性) -> 亮綠燈。
        - 燈二：Hook 2 (權限範圍) -> 根據你的 Scope 變換紅綠。
        - 燈三：Hook 3 (使用合規) -> 顯示檢核 `if Signed and Dispute`。
    3.  **右側輸出區：** 隨著選單切換，即時看到 `Payload` 欄位消失或出現。強調 `M12 Controller` 的「最後防禦」邏輯。

---

## 提案三：【One Spine 的時間旅程：從偵測到結案】(State Machine Journey)

**核心思想：** 展示「同一個數據主幹（One Spine）」，在不同時間節點對不同角色的投影。

*   **Demo 方式：**
    1.  **起點：事件發生。** 系統生成最完整的數據主幹。
    2.  **旅程節點一 (設備端)：** 展示 `gate_ref` 標註為 `EG-STRICT-V2`。這證明了「隱私在源頭就被執行」。
    3.  **旅程節點二 (客服檢視)：** 展示輸出包。這時 `pc_priv` 為 `NULL`。重點強調：並非資料遺失，而是「系統主動剝離以保護用戶」。
    4.  **旅程節點三 (證據導出)：** 展示最終 Bundle 包。當所有選項 (`Dispute` + `Signed`) 滿足時，`pc_priv` 被「解凍」。

---

## 總結：Demo 的核心台詞 (Golden Message)

> 「在 One Spine 架構下，數據不再是死板的開關。我們根據**你的身分 (Scope)**、**你的意圖 (Context)** 以及**數據的信度 (Sign)**，在出口處精準、動態地調節資料流向。這就是我們賦予 DAE P1 的隱私智能。」
