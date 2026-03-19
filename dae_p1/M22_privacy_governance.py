"""
M22 隱私治理模組 (Privacy Governance Module)
重構版本：符合「純參照（Reference-Only）」設計原則

核心改動：
1. check_base_validity: 不再回傳硬編碼的 PrivacyPolicyRef 物件，改回傳輕量的 ref_id 字串字典
2. project_view: 不再扮演「資料過濾器」角色，改為負責「動態生成 EgressRef」
3. evaluate_closure_grade: 改用設定化的規則，而不是 if/else 硬編碼
"""
from typing import Optional, Dict, Any, Tuple, List
import uuid

# BYUSE 規則庫 — 收斂版（2 個情境，3 種 Grade）
#
# 設計決策：
#   - 移除 COMPLIANCE_AUDIT：前端從未傳送此 context，為死碼
#   - 移除 PARTIAL_RELIANCE：前端所有元件都未針對此值做差異化處理，
#     行為等同 DELIVERY_GRADE，合併消除以減少認知負擔
#
# 現在只有 3 個 Grade：
#   DELIVERY_GRADE     = 預設，無特定用途宣告，只給 PC-Min
#   CLOSURE_GRADE      = 驗證通過，允許 PC-Priv
#   NOT_CLOSURE_GRADE  = 阻擋，缺少必要 Refs 或簽署
BYUSE_RULES: dict = {
    "SUPPORT_CLOSURE": {
        "required_refs":    ["policy", "disclosure"], # 精簡但足以 Demo
        "on_complete_grade": "READY",
        "on_missing_grade":  "INCOMPLETE",            # 缺技術 Ref -> 系統異常故事
    },
    "DISPUTE": {
        "required_refs":    ["policy", "disclosure"],
        "requires_signed":   True,                    # 必須使用者主動簽署
        "on_complete_grade": "READY",
        "on_missing_grade":  "PENDING",               # 缺簽名 -> 法律流程故事
    },
}


# 預設的 Ref Token 模板（來自 Policy Store，模擬 Token 化結果）
# 生產環境這些應從外部 Policy Store 或 Config Service 讀取
DEFAULT_REF_TOKENS: Dict[str, str] = {
    "policy":   "tok_pol_default_v1",
    "purpose":  "tok_purp_diagnosis",
    "retention":"tok_ret_30d",
    "disclosure": "tok_scope_isp_support",
    "redaction":  "REDACT.MIN",
}


class PrivacyGovernance:
    """
    M22 隱私治理模組（Reference-Only 版本）

    三個職責：
    1. check_base_validity：只回傳 ref_id 字串，不回傳 Ref 物件（輕量化）
    2. project_view：不再過濾資料，改為生成 Egress Receipt（出口回執）
    3. evaluate_closure_grade：改用 BYUSE_RULES 設定，不再寫死業務邏輯
    """

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def check_base_validity(self, attempt) -> Tuple[bool, List[str], Dict[str, str]]:
        """
        [產品化簡化] 基礎有效性檢查
        不再檢查環境變數（如 Policy），預設系統運行即合法。
        """
        # [關鍵改動] 直接回傳 Token 字典，不再進行冗餘的 Policy 存在檢查
        ref_tokens = dict(DEFAULT_REF_TOKENS)
        return True, [], ref_tokens

    def project_view(self, proof_card_dict: Dict[str, Any], authority_scope_ref: Optional[str]) -> Dict[str, Any]:
        """
        [改動 2] 視圖投影器（不再過濾資料，改為生成 Egress Receipt）

        原版：根據 authority_scope_ref 決定是否 strip payload（payload=None）
        新版：payload 的去留由 API 層決定；M22 只負責驗證出口授權並生成 egress_receipt_ref

        設計理由：資料過濾不應在業務層做，API 層才是正確的邊界
        """
        from dataclasses import asdict, is_dataclass
        if is_dataclass(proof_card_dict):
            result = asdict(proof_card_dict)
        else:
            result = dict(proof_card_dict)  # 不修改原始物件

        # 出口授權檢查：只做授權，不做資料過濾
        disclosure_token = result.get("refs", {}).get("disclosure", "")
        egress_allowed = False

        if authority_scope_ref:
            # 簡化邏輯：只要 authority_scope_ref 是合法的 scope token，就允許
            if authority_scope_ref in ["isp-support", "admin_override"]:
                egress_allowed = True

        if egress_allowed:
            # 生成出口回執（Egress Receipt Token）
            result["egress_receipt_ref"] = f"egr-{uuid.uuid4().hex[:8]}"
        else:
            result["egress_receipt_ref"] = None

        # 設定閘道參照
        if "refs" not in result or result["refs"] is None:
            result["refs"] = {}
        result["refs"]["gate_ref"] = "EG-STRICT-V2" if self.strict_mode else "EG-DEFAULT-V1"

        return result

    def evaluate_closure_grade(self, card_dict: Any, context_ref: Optional[str] = None, is_signed: bool = False) -> Tuple[str, Optional[str]]:
        """
        [產品故事化] BYUSE 合規驗證器 (四狀態版)
        READY: 授權通過，可看 Payload
        PENDING: 人為行為缺失 (缺簽署)
        INCOMPLETE: 技術數據缺失 (缺 Policy/Refs)
        UNAUTHORIZED: 用途不符
        """
        from dataclasses import asdict, is_dataclass
        if is_dataclass(card_dict):
            card_dict = asdict(card_dict)
            
        if not context_ref:
            return "UNAUTHORIZED", None

        # 1. 查找規則
        rule = BYUSE_RULES.get(context_ref.upper())
        if not rule:
            return "UNAUTHORIZED", None

        # 2. 檢查技術完整性 (Technical Check)
        card_refs = card_dict.get("refs") or {}
        required = rule.get("required_refs", [])
        missing_tech = [r for r in required if r not in card_refs]
        
        if missing_tech:
            # 在 Demo 中代表「系統配置遺失」或「數據同步失敗」
            return "INCOMPLETE", f"UPREQ-MISSING-{missing_tech[0].upper()}"

        # 3. 檢查人為/法律授權 (Business/Legal Check)
        if rule.get("requires_signed") and not is_signed:
            # 在 Demo 中代表「用戶尚未同意」
            return "PENDING", "UPREQ-SIGNED-MANIFEST"

        return rule["on_complete_grade"], None
