# ProofCard V1.3 to V1.4 變更差異分析 (Diff)

本文件摘要從 `ProofCard_Free_V1.3_Spec.md` 升級至 `ProofCard_Free_V1.4_Spec.md` (引入 BREL Privacy Hooks) 的主要變更。

## 1. 核心原則 (Section 1) 增訂
- **新增 P6｜隱私門控 (Privacy Precondition)**：將隱私合規性視為 ProofCard 有效性的先決條件。
- **新增 P7｜出口治理 (Egress Control)**：引入 Egress Gate，預設僅允許送出 PC-Min。
- **新增 P8｜BYUSE 升級牽引 (Partial Reliance)**：定義被用於客服/賠付等場景時，自動拉高憑證要求。

## 2. 審查與判定管道 (新增 Section 2)
在原有的架構前插入 BREL Pipeline 概念：
- 新增 `Privacy Validity Check` (Admission 階段檢查)。
- 新增 `Minimal-Disclosure Egress Gate` (輸出階段檢查)。
- 新增 `BYUSE` 動態升級邏輯。

## 3. ProofCard 欄位結構大幅重構 (Section 3)
原 V1.3 的單一 ProofCard 結構，拆分為**雙層式區塊**：
- **廢除**原表單中的單層陳述，改為 `min` 與 `priv` 兩個區塊。
- **PC-Min (外送層) 新增欄位**：
  - `admission_verdict` (ADMIT/DENY/DEGRADE)
  - `admission_effect`
  - `privacy_check_verdict`
  - `egress_receipt_ref`
  - `byuse_context_ref`
- **PC-Priv (內部層) 新增欄位** (全為 Privacy 相關 Reference)：
  - `privacy_policy_ref`
  - `purpose_ref`
  - `retention_ref`
  - `disclosure_scope_ref`
  - `redaction_profile_ref`
  - `privacy_violation_flag` / `privacy_violation_reason_code`

## 4. 合規檢查表 (Section 7) 增訂
要求 Free-tier CPE 必須實作 PC-Min / PC-Priv 分層、Privacy Check、Egress Gate 以及 BYUSE 動態升級要求。
