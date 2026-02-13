
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from .M00_common import EpisodeRecognition, iso, ProofCardMin, ProofCardPriv, AdmissionVerdict, EvidenceGrade, asdict
from .M10_timeline_builder import TimelineBuilder
from .M11_bundle_exporter import BundleExporter
from .M22_privacy_governance import PrivacyGovernance
from enum import Enum

def _safe_serialize(obj):
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return _safe_serialize(asdict(obj))
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_serialize(v) for v in obj]
    return obj

@dataclass
class OBHResult:
    episode_id: str
    exported_path: str
    bundle_content: Optional[Dict[str, Any]] = None

class OBHController:
    """
    One-Button Help (OBH): TRIGGER -> M13 GENERATE -> M22 EGRESS -> EXPORT.
    Refactored for Unified Privacy Architecture (One Spine).
    """
    def __init__(self, exporter: BundleExporter):
        self.exporter = exporter
        self.last_result: Optional[OBHResult] = None
        # M12 controls the Egress, M13 controls internal hooks
        self.governance = PrivacyGovernance(strict_mode=False)
        
        # [NEW] Use ProofCardGenerator (M13)
        from .M13_fp_lite import ProofCardGenerator
        self.pc_generator = ProofCardGenerator()

    def run(self, out_dir: str, recognition: EpisodeRecognition,
            metrics: List[Any], events: List[Any], snapshots: List[Any],
            byuse_context_ref: Optional[str] = None,
            authority_scope_ref: Optional[str] = None) -> OBHResult:
        
        # 1. Generate Unified ProofCard (includes Hook 1-3 + Freeze)
        # We pass the raw data objects to M13
        full_card = self.pc_generator.generate(
            metrics=metrics,
            events=events,
            snapshots=snapshots,
            profile_ref="WIFI78_INSTALL_ACCEPT", # Configurable?
            window_ref_str=recognition.worst_window_ref or "W-LATEST",
            authority_scope_ref=authority_scope_ref,
            byuse_context_ref=byuse_context_ref
        )
        
        # 2. Pipeline: Egress Gate (Hook 4)
        # Decide what actually leaves
        final_min, final_priv = self.governance.egress_gate(
            full_card.pc_min, full_card.pc_priv, authority_scope_ref
        )
        
        # 3. Assemble Final Bundle Dict
        bundle = {
            "spec": "DAE_P1_Priv_v2",
            "proof_card_min": _safe_serialize(final_min),
            "proof_card_priv": _safe_serialize(final_priv) if final_priv else None,
        }
        
        # Extract/Embed Logic based on Privacy
        # Extract/Embed Logic based on Privacy
        # Base shim from PC-Min (Always Safe)
        v13_shim = {
            "verdict": full_card.pc_min.primary_verdict.value if hasattr(full_card.pc_min.primary_verdict, "value") else full_card.pc_min.primary_verdict,
            "evidence_grade": full_card.pc_min.evidence_grade.value if hasattr(full_card.pc_min.evidence_grade, "value") else full_card.pc_min.evidence_grade,
            "admission_verdict": full_card.pc_min.admission_verdict.value if hasattr(full_card.pc_min.admission_verdict, "value") else full_card.pc_min.admission_verdict,
            "privacy_check_verdict": full_card.pc_min.privacy_check_verdict.value if hasattr(full_card.pc_min.privacy_check_verdict, "value") else full_card.pc_min.privacy_check_verdict,
            "episode_id": full_card.pc_min.episode_id,
            "window_ref": full_card.pc_min.window_ref,
            "gate_ref": full_card.pc_min.gate_ref,
            "data_range_start": full_card.pc_min.data_range_start,
            "data_range_end": full_card.pc_min.data_range_end,
        }
        


        if final_priv:
            # We have access to sensitive data
            frozen = final_priv.frozen_timeline or {}
            bundle["payload"] = {
                "timeline": frozen.get("timeline"),
                "engineering_proof": frozen.get("engineering_proof"),
                "observability": asdict(recognition.observability), 
                "evidence_refs": recognition.evidence_refs
            }
            # [INTEGRATION SUPPORT]
            # Merge Engineering Proof into Shim
            eng_proof = frozen.get("engineering_proof", {})
            v13_shim.update(eng_proof)
        else:
            bundle["payload"] = "REDACTED: PRE-ADMISSION or UNAUTHORIZED"
            
        bundle["proof_card_v13"] = v13_shim
        
        path = self.exporter.export(out_dir, recognition.episode_id, bundle)
        
        # Safe serialize
        safe_bundle = _safe_serialize(bundle)
            
        res = OBHResult(episode_id=recognition.episode_id, exported_path=path, bundle_content=safe_bundle)
        self.last_result = res
        return res
