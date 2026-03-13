# DAE P1 (19 Modules) - V1.4 新版亮點 Demo 流程與講稿 🎙️

這份 Demo 指南專為展示我們「Cable (DOCSIS) 診斷無縫銜接」以及全新開發的「PC-Priv 隱私守門員自動脫敏」兩大架構亮點所設計。

---

## 預先準備 (Pre-flight Checklist)
1. **啟動後端引擎**：確認 terminal 運行著 `python server.py`。
2. **啟動 App**：確保 React Native 手機 App 在模擬器或實機上開啓，停留在首頁 (Home Dashboard)。

---

## 🎬 情境一：展現系統的彈性與智慧 (The Cable Incident)
**📍 動作：** 停留在 App 首頁 (Home Dashboard)
**💬 講稿：**
> 「各位長官好，現在大家看到的是客服端的最外層首頁。
> 過去的診斷系統，只要一換底層硬體——例如從 Wi-Fi 換到光纖或 Cable，後端的判定邏輯就得全部重寫，導致維護成本極高。
> 
> 但在我們這套最新的 DAE P1 (19 Modules) 引擎裡，我們做到了**完全解耦**。
> 現在，我將啟動一個『模擬的 Cable (有線電視上網) 設備客訴』。大家可以注意看，系統如何聰明地『切換大腦』。」

**📍 動作：** 在首頁的頂部測試按鈕列，點擊 **[Simulate Cable Incident]** 
*(註：這時後端的 Core Loop 會瞬間把環境變數 `domain` 抽換成 `CABLE`，並注入 T3/T4 Timeout、MER 爆低等 Cable 專屬異常數據)*

**💬 講稿：**
> 「好了，現在後端已經收到來自這台 Cable 數據機回報的底層雜訊。
> 接下來，讓我們以客服人員的角度，進入『CSR Support Console』來查修。」

---

## 🎬 情境二：一針見血的診斷與 Mapping Table 的威力
**📍 動作：** 點擊進入 **CSR Support Console (第二個選單)**，畫面列出設備總覽。找到 **Edge Modem (DOCSIS)** 這台機器，點進它。
**💬 講稿：**
> 「當客服點進這台 Cable 設備時，大家看！系統沒有被 Wi-Fi 的『干擾、擁塞』等舊規則綁架。
> 
> 我們的 **Install Verifier (M20安裝驗證器)** 瞬間察覺這是一台 Cable 設備，它自動抽換了後台的判定 Profile 為 `CABLE_INSTALL_ACCEPT`。
> 並且，透過我們剛開發的**全局診斷字典 (Diagnosis Mapping Table)**，系統非常精準地把底層生硬的 `ReasonCode`，直接翻譯成客服看得懂的人話——**『CABLE PLANT ISSUE (實體線路異常)』**！」

**📍 動作：** 滑動一下畫面，展示出現了 `ofdm_mer_db` 與 `us_rtt_ms` (上行延遲) 的 Facet 數據積木。
**💬 講稿：**
> 「各位看下面的數據亮點 (Outcome Facet)，畫面上拋棄了 Wi-Fi 專用的干擾重傳率，改為秀出影響 Cable 上網最致命的 **OFDM MER (雜訊比)** 與 **T3/T4 Timeout** 數值。一秒鐘，客服就知道要派工去查外線，不用再大海撈針！」

---

## 🎬 情境三：重頭戲！PC-Min 與 PC-Priv 聯手防護 🛡️
**📍 動作：** 點擊設備底層的 **[Generate ProofCard (OBH)]** 按鈕。等待幾秒，跳出白底的「DAE Proof Card V1.3」畫面。
**💬 講稿：**
> 「接下來，是最核心的合規亮點。
> 當客服點下『一鍵產出證據卡 (OBH)』，要求保存這份查修紀錄時，我們要怎麼證明這份證據是合規的、沒有偷夾帶客戶私隱的？
> 
> 請大家看畫面最下方的全新區塊：**『🛡️ Privacy & Compliance (PC-Priv)』**。」

**📍 動作：** 將 App 畫面往下捲動，停在 **PC-Priv** 綠色的狀態框。
**💬 講稿：**
> 「這就是我們最新的 **隱私守門員 (M22 Privacy Governance)** 的運作成果。
> 大家可以看到這張卡片上，清清楚楚地印著防偽標籤：
> * **Authorized Purpose**: Diagnosis (本資料僅限除錯使用)
> * **Disclosure**: isp-support (僅向 ISP 客服揭露)
> * **Redaction Level**: REDACT.MIN (執行最低限度脫敏)
> 
> 最重要的是，請看 **Egress Receipt (匯出收據碼)**，這裡顯示的是 **'None (Payload Stripped)'**（用安全的綠色顯示）。
> 
> 這代表什麼？這代表系統**知道現在看報告的是權限較低的客服人員，所以它非常盡責地在發出報告前，直接把最底層、最機密、可能洩漏用戶作息的『每秒時序數據矩陣 (Engineering Payload)』給全部砍掉了**！
> 
> 系統只留下上面那幾顆經過數學 p95 運算後的安全答案給客服看。沒有人能看到不該看的原始數據，這就是做到極致的 Min-Disclosure (最小揭露原則) 設計！」

---

## 結語
**💬 講稿：**
> 「透過這次的架構升級，我們不只證明了 DAE 19 Modules 可以無縫支援跨網路線路 (Wi-Fi / FWA / Cable) 的混合診斷，更把企業級的資安與個資保護 (PC-Priv) 直接內建在資料流出的最後一道防線。以上是我的展示！」
