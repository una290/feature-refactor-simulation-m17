from typing import Optional, Dict, Any, Tuple
from .M00_common import (
    EpisodeRecognition, AdmissionVerdict, EvidenceGrade, 
    PrivacyPolicyRef, PurposeRef, RetentionRef, DisclosureScopeRef,
    ProofCardMin, ProofCardPriv, iso
)

class PrivacyGovernance:
    """
    M22 Privacy Governance Module
    Implements the 'One Spine' governance logic:
    1. Privacy Check (Hooks)
    2. BYUSE Qualification
    3. Admission Decision
    4. Egress Gating
    """
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def privacy_check(self, attempt: EpisodeRecognition) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Hook 1: Privacy Check (Validity)
        Checks if the attempt is valid under the profile's privacy policy.
        """
        # 1. Open Set Check: Does this profile imply sensitive data?
        # Assumption: All profiles in this simulation are "Managed" and thus sensitive.
        # In a real system, we'd check if attempt.profile_ref in SENSITIVE_PROFILES
        
        missing = attempt.observability.missing_refs
        if missing:
            # Check for critical privacy governance refs
            # We assume 'policy' and 'disclosure' are critical.
            # (In M00 ObservabilityResult, missing_refs is a list of strings)
            # If any privacy-related ref is missing (simulated by checking if list is non-empty for now)
            # In a real system, we would parse the specific missing refs.
            return False, f"Missing Critical Refs: {missing}", None
        
        # 2. Validity Check: Are the refs valid? (Simulated)
        # We assume if they are present (observability sufficient), they are valid.
        
        # 3. Construct the explicit refs for the ProofCardPriv
        # In this simulation, we hardcode a 'standard' set if everything is OK.
        # In production, these come from the Policy Registry based on the snapshot_ref.
        refs = {
            "policy": PrivacyPolicyRef(policy_id="pol-default"),
            "purpose": PurposeRef(purpose_id="diagnosis"),
            "retention": RetentionRef(policy_id="ret-30d"),
            "disclosure": DisclosureScopeRef(scope_id="isp-support"),
            "redaction": "REDACT.MIN"
        }
        return True, "OK", refs

    def byuse_qualify(self, context_ref: Optional[str], current_grade: EvidenceGrade) -> Tuple[EvidenceGrade, Optional[str]]:
        """
        Hook 2: BYUSE Upgrade
        If byuse_context_ref is set (e.g. 'CSR', 'REGULATOR'), enforce higher standards.
        Returns: (New EvidenceGrade, UpgradeRequirementsRef)
        """
        if not context_ref:
            # Default usage (no specific reliance context) -> Delivery Grade is fine
            return current_grade, None
            
        # BYUSE Logic:
        # If context is High Reliance (e.g., 'dispute_resolution'), we require explicit 'window_policy_id'
        # In this simulation, let's say 'dispute' context requires it.
        
        if "dispute" in context_ref or "compliance" in context_ref:
            # Check if we have what's needed. 
            # For simulation, we assume if we are here, we might be missing something unless we did a fetch.
            # Let's simulate a condition: if current_grade is NOT already high enough?
            # Or simpler: always demand an upgrade if it's a dispute, unless we verify we have it.
            # Let's assume we are missing a specific 'signed_manifest' for disputes.
            
            return EvidenceGrade.NOT_CLOSURE_GRADE, "UPREQ-SIGNED-MANIFEST"
             
        return current_grade, None

    def admission_decide(self, privacy_passed: bool, byuse_grade: EvidenceGrade) -> Tuple[AdmissionVerdict, str, EvidenceGrade]:
        """
        Hook 3: Admission Decide
        Decides: Verdict, Effect, Final Grade.
        """
        if not privacy_passed:
            if self.strict_mode:
                return AdmissionVerdict.DENY, "NONE", EvidenceGrade.NOT_CLOSURE_GRADE
            else:
                return AdmissionVerdict.DEGRADE, "scope_reduction", EvidenceGrade.PARTIAL_RELIANCE
        
        # If privacy passed
        if byuse_grade == EvidenceGrade.NOT_CLOSURE_GRADE:
             # Admitted, but flagged as not suitable for closure
             return AdmissionVerdict.ADMIT, "freeze_egress", EvidenceGrade.NOT_CLOSURE_GRADE
             
        # Happy path
        return AdmissionVerdict.ADMIT, "none", EvidenceGrade.DELIVERY_GRADE

    def egress_gate(self, pc_min: ProofCardMin, pc_priv: Optional[ProofCardPriv], authority_scope_ref: Optional[str]) -> Tuple[ProofCardMin, Optional[ProofCardPriv]]:
        """
        Hook 4: Egress Gate (Minimal-Disclosure)
        Standard: PC-Min always goes. PC-Priv only goes if authorized.
        """
        import uuid
        
        # 1. Assign Gate Reference (The "Stamp")
        # In a real system, this depends on the active Egress Policy.
        # We use strict_mode to simulate different gates.
        if self.strict_mode:
            current_gate = "EG-STRICT-V2" 
        else:
            current_gate = "EG-DEFAULT-V1"
            
        pc_min.gate_ref = current_gate
        
        # 2. Assign Policy Snapshot Ref (Propagate from Priv or Default)
        if pc_priv and pc_priv.privacy_policy_ref:
            # Construct a snapshot string (e.g., "POL-DEFAULT-V1.0")
            pc_min.policy_snapshot_ref = f"{pc_priv.privacy_policy_ref.policy_id.upper()}-V{pc_priv.privacy_policy_ref.version}"
        elif not pc_min.policy_snapshot_ref or pc_min.policy_snapshot_ref == "PP-V1.0":
             # If it's still the default from M13, try to be more specific if possible, 
             # otherwise keep the placeholder.
             pass

        # 3. Check Admissibility for Priv
        if not pc_priv:
            return pc_min, None
            
        if pc_min.admission_verdict == AdmissionVerdict.DENY:
             # Should practically not happen here if caller respects flow, but safety check
            return pc_min, None
            
        # 3. Privacy Gate Logic
        # Rule: allowed if authority_scope_ref matches priv.disclosure_scope_ref
        allowed = False
        if authority_scope_ref and pc_priv.disclosure_scope_ref:
            # Simple string match simulation
            # In (v2.0), we check if authority 'covers' the disclosure scope
            if authority_scope_ref == pc_priv.disclosure_scope_ref.scope_id:
                allowed = True
            elif authority_scope_ref == "admin_override":
                allowed = True
        
        if allowed:
            return pc_min, pc_priv
        else:
            # Strip Priv
            return pc_min, None

