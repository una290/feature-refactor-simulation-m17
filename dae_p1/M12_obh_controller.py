
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .M00_common import EpisodeRecognition, iso, ProofCardMin, ProofCardPriv, AdmissionVerdict, EvidenceGrade, asdict
from .M10_timeline_builder import TimelineBuilder
from .M11_bundle_exporter import BundleExporter
from .M22_privacy_governance import PrivacyGovernance

@dataclass
class OBHResult:
    episode_id: str
    exported_path: str
    bundle_content: Optional[Dict[str, Any]] = None

class OBHController:
    """
    One-Button Help (OBH): FREEZE_BUFFER + GENERATE_TIMELINE + EXPORT_BUNDLE.
    Never changes network settings.
    """
    def __init__(self, timeline_builder: TimelineBuilder, exporter: BundleExporter):
        self.timeline_builder = timeline_builder
        self.exporter = exporter
        self.last_result: Optional[OBHResult] = None
        self.governance = PrivacyGovernance(strict_mode=False) # Configurable in real app

    def run(self, out_dir: str, recognition: EpisodeRecognition,
            metrics, events, snapshots, 
            byuse_context_ref: Optional[str] = None,
            authority_scope_ref: Optional[str] = None) -> OBHResult:
        
        # 1. Pipeline: Privacy Check
        passed, msg, policy_refs = self.governance.privacy_check(recognition)
        
        # 2. Pipeline: BYUSE Qualify
        # Determine the provisional grade based on observability or existing flow
        # For now, we assume DELIVERY_GRADE as baseline unless downgraded.
        tmp_grade = EvidenceGrade.DELIVERY_GRADE
        final_grade, upgrade_req = self.governance.byuse_qualify(byuse_context_ref, tmp_grade)
        
        # 3. Pipeline: Admission Decide
        adm_verdict, adm_effect, final_grade = self.governance.admission_decide(passed, final_grade)
        
        # 4. Build Proof Cards (Internal/Speculative)
        timeline = self.timeline_builder.build(metrics, events, snapshots)
        
        # Construct PC-Min
        # We need to map boolean passed to Enum
        # M00 defines PrivacyCheckVerdict
        try:
             # If we imported the Enum
             from .M00_common import PrivacyCheckVerdict
             priv_verdict = PrivacyCheckVerdict.PASS if passed else PrivacyCheckVerdict.FAIL
        except ImportError:
             priv_verdict = "PASS" if passed else "FAIL"

        pc_min = ProofCardMin(
            episode_id=recognition.episode_id,
            episode_start=iso(recognition.episode_start),
            primary_verdict=recognition.primary_verdict,
            admission_verdict=adm_verdict,
            admission_effect=adm_effect,
            privacy_check_verdict=priv_verdict,
            evidence_grade=final_grade,
            byuse_context_ref=byuse_context_ref
        )
        if upgrade_req:
             # Add to missing class or similar if we had a field. 
             # For now, relying on evidence_grade=NOT_CLOSURE_GRADE to signal it.
             pass
        
        # Construct PC-Priv (if we have refs)
        pc_priv = None
        if policy_refs:
             pc_priv = ProofCardPriv(
                 privacy_policy_ref=policy_refs.get("policy"),
                 purpose_ref=policy_refs.get("purpose"),
                 retention_ref=policy_refs.get("retention"),
                 disclosure_scope_ref=policy_refs.get("disclosure"),
                 redaction_profile_ref=policy_refs.get("redaction")
             )

        # 5. Pipeline: Egress Gate (The One Spine Check)
        # Decide what actually leaves
        final_min, final_priv = self.governance.egress_gate(pc_min, pc_priv, authority_scope_ref)
        
        # Assemble Final Bundle Dict
        bundle = {
            "spec": "DAE_P1_Priv_v2",
            "proof_card_min": asdict(final_min),
            "proof_card_priv": asdict(final_priv) if final_priv else None,
        }
        
        if final_priv:
            bundle["payload"] = {
                "timeline": timeline,
                "observability": asdict(recognition.observability), 
                "evidence_refs": recognition.evidence_refs
            }
        else:
            bundle["payload"] = "REDACTED: PRE-ADMISSION or UNAUTHORIZED"
            
        path = self.exporter.export(out_dir, recognition.episode_id, bundle)
        res = OBHResult(episode_id=recognition.episode_id, exported_path=path, bundle_content=bundle)
        self.last_result = res
        return res
