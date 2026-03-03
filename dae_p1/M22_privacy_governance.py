from typing import Optional, Dict, Any, Tuple, List
from .M00_common import (
    EpisodeRecognition, 
    PrivacyPolicyRef, PurposeRef, RetentionRef, DisclosureScopeRef,
    ProofCard, iso
)

class PrivacyGovernance:
    """
    M22 Privacy Governance Module
    Implements the 'Capability-Based View' logic:
    1. Base Validity Check
    2. View Projection
    3. BYUSE Compliance Validator
    """
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def check_base_validity(self, attempt: EpisodeRecognition) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Hook 1: Base Validity
        Checks if the attempt is valid under the profile's privacy policy.
        Returns: (is_valid, missing_evidence_classes, explicit_refs_dict)
        """
        missing_classes = []
        # In a real system, we'd check if attempt.profile_ref in SENSITIVE_PROFILES
        
        missing = attempt.observability.missing_refs
        if missing:
            missing_classes.append("PRIVACY_POLICY_MISSING")
            return False, missing_classes, {}
        
        # 3. Construct the explicit refs for the ProofCard
        # In this simulation, we hardcode a 'standard' set if everything is OK.
        refs = {
            "policy": PrivacyPolicyRef(policy_id="pol-default"),
            "purpose": PurposeRef(purpose_id="diagnosis"),
            "retention": RetentionRef(policy_id="ret-30d"),
            "disclosure": DisclosureScopeRef(scope_id="isp-support"),
            "redaction": "REDACT.MIN"
        }
        return True, [], refs

    def project_view(self, proof_card: ProofCard, authority_scope_ref: Optional[str]) -> Dict[str, Any]:
        """
        Hook 2: View Projector (Egress Gate / Min-Disclosure)
        Project the objective ProofCard into a JSON bundle based on the requested scope.
        """
        from dataclasses import asdict
        import uuid
        
        card_dict = asdict(proof_card)
        
        # Rule: allowed if authority_scope_ref matches priv.disclosure_scope_ref
        allowed = False
        refs_dict = card_dict.get("refs", {})
        disc_ref = refs_dict.get("disclosure")
        
        if authority_scope_ref and disc_ref:
            scope_str = disc_ref.get("scope_id") if isinstance(disc_ref, dict) else (disc_ref.scope_id if hasattr(disc_ref, "scope_id") else None)
            if authority_scope_ref == scope_str:
                allowed = True
            elif authority_scope_ref == "admin_override":
                allowed = True

        if allowed:
            # Generate egress receipt only when sensitive payload is exported
            card_dict["egress_receipt_ref"] = f"EGRESS-REC-{uuid.uuid4().hex[:8]}"
        else:
            # Strip Sensitive Payload (Eqv to PC-Min output)
            card_dict["payload"] = None
            card_dict["egress_receipt_ref"] = None

        # Set gate reference dynamically
        card_dict["refs"]["gate_ref"] = "EG-STRICT-V2" if self.strict_mode else "EG-DEFAULT-V1"

        return card_dict

    def evaluate_closure_grade(self, proof_card_dict: Dict[str, Any], context_ref: str, is_signed: bool = False) -> Tuple[str, Optional[str]]:
        """
        Hook 3: BYUSE Compliance Validator
        Given a context (e.g., 'SUPPORT_CLOSURE', 'DISPUTE'), evaluate if the card has the necessary refs.
        """
        if not context_ref:
            # Default usage (no specific reliance context) -> Delivery Grade is fine
            return "DELIVERY_GRADE", None
            
        # BYUSE Logic:
        # If context is High Reliance (e.g., 'dispute', 'compliance'), we require explicit 'signed_manifest'
        if "dispute" in context_ref or "compliance" in context_ref:
            if is_signed:
                return "CLOSURE_GRADE", None
            else:
                return "NOT_CLOSURE_GRADE", "UPREQ-SIGNED-MANIFEST"
             
        return "DELIVERY_GRADE", None

