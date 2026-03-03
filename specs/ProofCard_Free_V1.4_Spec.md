# DAE ProofCard Free on CPE — 工程規格書 V1.4（Wi‑Fi 7/8 + FWA + Cable + BREL Privacy）

版本：V1.4（Normative / 規範性）
目的：基於 V1.3 的「最小可採信結案收據」，正式引入 BREL (One Spine) 的「隱私掛鉤 (Privacy Hooks)」、「分層揭露 (PC-Min/PC-Priv)」與「BYUSE 動態升級要求」，確保在不檢查 Payload 的情況下，能做跨域、跨供應商的安全證據交換。

## 0. 適用範圍

本規格定義 Free-tier CPE 產生的 ProofCard 必須遵循的資料結構與隱私門控規則。
支援：
• 消費者申訴/退貨/保固/爭議時的最低憑證
• 運營商 CSR / 工單結案時的最低對帳收據
• 供應鏈究責（晶片/韌體/雲管/回程）時的最小可調取索引
**• (V1.4 新增)** 跨供應鏈、跨網域資料交換時的「隱私門控 (Privacy Validity Precondition)」與「最小揭露出口閘 (Egress Gate)」。

## 1. 核心原則（必守）

P1｜收據性：任何會影響「可否結案/可否宣稱」的判定，必出且只出一張 ProofCard。
P2｜可否定：ProofCard 必須能被反駁與再計算；缺必要欄位即不得宣稱。
P3｜有效性：必包含權限/時效引用與有效性裁決（validity_verdict）。
P4｜可調取：平常只上報 ProofCard + manifest_ref；需爭議時才拉取 bundle 片段。
P5｜最小揭露：不要求 payload/內容；以 metadata 級統計與事件片段為主。
**P6｜隱私門控 (Privacy as Precondition)：** 只要涉及「可能影響可識別流」，必須附帶隱私政策引用 (policy refs)，否則一律降級 (DEGRADE) 或拒絕 (DENY)。
**P7｜出口治理 (Egress Control)：** 預設僅允許外送最小化資料 (PC-Min)。任何 PC-Priv 級別的輸出都必須經過 Egress Gate 核准並產生回執 (egress_receipt_ref)。
**P8｜BYUSE 升級牽引 (Partial Reliance)：** 只要證據被用於「結案/賠付/監管」(BYUSE)，即自動觸發嚴格認證 (Requiredness)，欠缺憑證則判定為 `not-closure-grade` 並拒絕升級。

## 2. 審查與判定管道 (BREL Pipeline)

判定流程擴展為加入隱私鉤子的標準 Pipeline：
`Ingest Attempt` → `privacy_check()` → `byuse_qualify()` → `admission_decide()` → `build_proof_card()` → `egress_gate()` 

### 2.1 Privacy Validity Check (Admission 前置把關)
不檢查 Payload 內容（非 DLP），僅檢查 policy refs 的存在性與時效性：
- 檢查 `privacy_policy_ref`、`disclosure_scope_ref` 等是否存在且非 stale。
- 若 FAIL，`min.admission_verdict` = `DENY` 或 `DEGRADE`，且 `reason_code` = `RC_PRIVACY_FAIL`。

### 2.2 Minimal-Disclosure Egress Gate
所有往系統外部送出的請求必須過 Egress Gate：
- 預設只放行 ProofCard **`min`** 區塊。
- 若需放行 **`priv`**，須具備 `authority_scope_ref` 與 `disclosure_scope_ref` 的雙重背書。
- 每次外送皆產生 `egress_receipt_ref` 寫回 ProofCard。

### 2.3 BYUSE 動態升級
當 `byuse_context_ref` 被觸發（例如客服調用 `SUPPORT_CLOSURE`）：
- 若所需 Refs (包含 privacy refs, window policy 等) 不全，證據等級(`evidence_grade`) 將降級為 `NOT_CLOSURE_GRADE`。
- 回傳 `upgrade_requirements_ref` 提示客戶端需補齊哪些資料。禁止事後用文字補齊。

## 3. ProofCard v1.4 資料結構 (分層式)

ProofCard 改為單卡雙區塊設計 (`min` 與 `priv`)，藉此滿足「四海皆準」的外送需求與受控的內部隱私需求。

### 3.1 核心通用屬性 (Core Attributes)
| 欄位 | 型別 | 必填 | 說明 |
| :--- | :--- | :--- | :--- |
| proof_card_ref | string | MUST | 本卡唯一識別碼 (ULID/UUID) |
| attempt_id | string | MUST | 觸發本次判定的事件或工單 ID |
| profile_ref | string | MUST | 判定情境（例如 WIFI78_INSTALL_ACCEPT） |
| enforcement_path_id | string | MUST | 承認路徑 / 流程路徑 |
| gate_ref | string | MUST | Admission Gate 參考標籤 |
| verdict | enum | MUST | READY / NOT_READY / INSUFFICIENT_EVIDENCE |
| evidence_grade | enum | MUST | DELIVERY_GRADE / PARTIAL_RELIANCE / NOT_CLOSURE_GRADE |
| window_ref | string | MUST | 取樣窗口 |
| reason_code[] | string[] | MUST | 判定原因 (包含 RC_PRIVACY_FAIL 等) |
| version_refs{} | object | MUST | version policy 集合 (policy_snapshot_ref, window_policy_id 等) |
| missing_evidence_class[] | string[]|OPTIONAL | 所缺失的證據類別 (例如 PRIVACY_POLICY_MISSING) |
| upgrade_requirements_ref | string | OPTIONAL | 若要求升格 BYUSE 所需補齊的指示參考 |

### 3.2 PC-Min (通用外送層)
對外開放，跨網域與跨供應商通用。不包含敏感政策與有效性規則細節。

| 欄位 | 型別 | 必填 | 說明 |
| :--- | :--- | :--- | :--- |
| admission_verdict | enum | MUST | ADMIT / DENY / DEGRADE |
| admission_effect | string | MUST | NONE / SLOW_MODE / EGRESS_MIN_ONLY / FREEZE_EGRESS |
| privacy_check_verdict | enum | MUST | PASS / FAIL / INCONCLUSIVE / NOT_APPLICABLE |
| egress_receipt_ref | string | OPTIONAL| 紀錄於 Egress Gate 允許外送特許資料時產生的回執編號 |
| byuse_context_ref | string | OPTIONAL| 觸發 Requiredness 的情境 (例如 SUPPORT_CLOSURE) |

### 3.3 PC-Priv (內部受控層)
預設不可外送，僅透過 Egress Gate 特許輸出。

| 欄位 | 型別 | 必填 | 說明 |
| :--- | :--- | :--- | :--- |
| privacy_policy_ref | string | MUST | 引用的隱私政策 (如 PRIV@v4) |
| purpose_ref | string | MUST | 取用目的 (如 PURP.NETWORK_OPERATION) |
| retention_ref | string | MUST | 保存期限要求 (例如 RET.7D) |
| disclosure_scope_ref | string | MUST | 允許的揭露範圍與粒度 (例如 SCOPE.MIN) |
| redaction_profile_ref | string | MUST | 套用的遮罩規則 (例如 REDACT.MAX) |
| privacy_violation_flag | bool | MUST | 是否違反任何內部隱私政策 |
| privacy_violation_reason_code[]|string[]|OPTIONAL| 違反細節代碼 |

## 4. Manifest（可調取索引）
(同 V1.3，由 manifest_ref 引用，列出 7 天內可取回的摘要與事件片段。)

## 5. p50/p95 (分位數計算規範)
(同 V1.3， Nearest-Rank 計算)

## 6. 各領域 Profile / Event Type 
(同 V1.3: Wi-Fi 7/8, FWA, Cable Modem)

## 7. 合規檢查表 (Pass/Fail)
Free-tier CPE 需達下列標準方能宣告 V1.4 合規：
1. 具備 PC-Min / PC-Priv 分層區隔，對外預設僅輸出 PC-Min。
2. 實作 Privacy Validity Check，任何欠缺隱私授權的 ProofCard 不得擁有 `ADMIT`。
3. 實作 Egress Gate，所有資料外送須檢查 `disclosure_scope_ref` 並具備 `egress_receipt_ref`。
4. 支援 BYUSE 動態升級，當被用於結案等情境時，必須要求完整的 privacy refs，否則回傳 `evidence_grade` = `NOT_CLOSURE_GRADE` 與 `missing_evidence_class`。
