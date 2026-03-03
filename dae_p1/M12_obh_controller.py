
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from .M00_common import EpisodeRecognition, iso, ProofCard, asdict
from .M10_timeline_builder import TimelineBuilder
from .M11_bundle_exporter import BundleExporter
from .M22_privacy_governance import PrivacyGovernance
from .M23_audit_logger import AuditLogger
import os
import pickle
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
        self.audit_logger = AuditLogger()
        
        # [NEW] Use ProofCardGenerator (M13)
        from .M13_fp_lite import ProofCardGenerator
        self.pc_generator = ProofCardGenerator()

        # Storage for Episode Retrieval Demo
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'saved_cards.pkl')
        self.saved_full_cards: Dict[str, ProofCard] = {}
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'rb') as f:
                    self.saved_full_cards = pickle.load(f)
            except Exception as e:
                print(f"[DEBUG M12] Failed to load from db: {e}")
                
        self.signed_manifests: set = set()

    def run(self, out_dir: str, recognition: EpisodeRecognition,
            metrics: List[Any], events: List[Any], snapshots: List[Any],
            byuse_context_ref: Optional[str] = None,
            authority_scope_ref: Optional[str] = None) -> OBHResult:
        
        from dataclasses import asdict
        
        # 1. Generate Unified ProofCard (Hook 1: Base Validity)
        full_card = self.pc_generator.generate(
            metrics=metrics,
            events=events,
            snapshots=snapshots,
            profile_ref="WIFI78_INSTALL_ACCEPT", # Configurable?
            window_ref_str=recognition.worst_window_ref or "W-LATEST",
            authority_scope_ref=authority_scope_ref,
            byuse_context_ref=byuse_context_ref,
            episode_id=recognition.episode_id
        )
        if full_card.payload:
            full_card.payload["observability"] = recognition.observability
            full_card.payload["evidence_refs"] = recognition.evidence_refs
            
        self.saved_full_cards[recognition.episode_id] = full_card
        print(f"[DEBUG M12] Saved full card for episode: '{recognition.episode_id}'")
        try:
            with open(self.db_path, 'wb') as f:
                pickle.dump(self.saved_full_cards, f)
        except Exception as e:
            print(f"[DEBUG M12] Failed to save to db: {e}")
            
        # 2. Pipeline: View Projector (Hook 2: Egress Filter)
        # Decide what actually leaves
        projected_card_dict = self.governance.project_view(full_card, authority_scope_ref)
        
        # 3. Pipeline: BYUSE Validator (Hook 3: Compliance Check)
        is_signed = recognition.episode_id in self.signed_manifests
        evidence_grade, upgrade_req = self.governance.evaluate_closure_grade(projected_card_dict, byuse_context_ref, is_signed=is_signed)
        
        # 4. Assemble Final Bundle Dict
        bundle = {
            "spec": "DAE_P1_Priv_v2_CapabilityBased",
            "proof_card": _safe_serialize(projected_card_dict),
            "evidence_grade": evidence_grade,
            "upgrade_requirements_ref": upgrade_req
        }
        
        # [NEW] Enforce Egress Gate on Payload
        is_dispute = byuse_context_ref and "dispute" in byuse_context_ref
        if not is_dispute or evidence_grade == "NOT_CLOSURE_GRADE":
            # Strip Sensitive Payload (Eqv to PC-Min output only)
            projected_card_dict["payload"] = None
            projected_card_dict["egress_receipt_ref"] = None
        
        # Extract/Embed Logic based on Privacy
        # Assembling PC-Min (Always Safe / External View)
        pc_min = {
            "verdict": projected_card_dict.get("primary_verdict"),
            "evidence_grade": evidence_grade,
            "episode_id": projected_card_dict.get("episode_id"),
            "window_ref": projected_card_dict.get("window_ref"),
            "data_range_start": projected_card_dict.get("data_range_start"),
            "data_range_end": projected_card_dict.get("data_range_end"),
            "missing_evidence_class": projected_card_dict.get("missing_evidence_class", []),
            "upgrade_requirements_ref": upgrade_req,
            "egress_receipt_ref": projected_card_dict.get("egress_receipt_ref")
        }
        
        payload = projected_card_dict.get("payload")
        if payload:
            # We have full view access, assemble PC-Priv
            pc_priv = {
                "timeline": payload.get("timeline"),
                "engineering_proof": payload.get("engineering_proof"),
                "observability": asdict(recognition.observability), 
                "evidence_refs": recognition.evidence_refs
            }
            # [INTEGRATION SUPPORT] Merge Engineering Proof into PC-Min if desired
            # or keep it strictly separated. Let's merge for UI compatibility.
            eng_proof = payload.get("engineering_proof", {})
            pc_min.update(eng_proof)
        else:
            pc_priv = None
            
        bundle["pc_min"] = pc_min
        bundle["pc_priv"] = pc_priv
        
        path = self.exporter.export(out_dir, recognition.episode_id, bundle)
        
        # [NEW] Audit Logging Persistence
        self.audit_logger.log_egress(
            episode_id=recognition.episode_id,
            authority_scope_ref=authority_scope_ref,
            egress_receipt_ref=projected_card_dict.get("egress_receipt_ref"),
            policy_snapshot_ref=projected_card_dict.get("refs", {}).get("policy", {}).get("policy_id", "UNKNOWN"),
            context_ref=byuse_context_ref,
            evidence_grade=evidence_grade
        )

        # Safe serialize
        safe_bundle = _safe_serialize(bundle)
            
        res = OBHResult(episode_id=recognition.episode_id, exported_path=path, bundle_content=safe_bundle)
        self.last_result = res
        return res

    def retrieve_bundle(self, episode_id: str, byuse_context_ref: Optional[str] = None, authority_scope_ref: Optional[str] = None):
        """Dynamically retrieve and re-project an existing proof card."""
        from dataclasses import asdict
        from .M12_obh_controller import _safe_serialize
        
        print(f"[DEBUG M12] Request to retrieve episode: '{episode_id}'")
        print(f"[DEBUG M12] Saved episodes in memory/db: {list(self.saved_full_cards.keys())}")
        
        full_card = self.saved_full_cards.get(episode_id)
        if not full_card:
            print(f"[DEBUG M12] Episode '{episode_id}' not found in saved_full_cards dict.")
            return None
            
        projected_card_dict = self.governance.project_view(full_card, authority_scope_ref)
        is_signed = episode_id in self.signed_manifests
        evidence_grade, upgrade_req = self.governance.evaluate_closure_grade(projected_card_dict, byuse_context_ref, is_signed=is_signed)
        
        bundle = {
            "spec": "DAE_P1_Priv_v2_CapabilityBased",
            "proof_card": _safe_serialize(projected_card_dict),
            "evidence_grade": evidence_grade,
            "upgrade_requirements_ref": upgrade_req
        }

        # [NEW] Enforce Egress Gate on Payload
        is_dispute = byuse_context_ref and "dispute" in byuse_context_ref
        if not is_dispute or evidence_grade == "NOT_CLOSURE_GRADE":
            # Strip Sensitive Payload (Eqv to PC-Min output only)
            projected_card_dict["payload"] = None
            projected_card_dict["egress_receipt_ref"] = None
        
        pc_min = {
            "verdict": projected_card_dict.get("primary_verdict"),
            "evidence_grade": evidence_grade,
            "episode_id": projected_card_dict.get("episode_id"),
            "window_ref": projected_card_dict.get("window_ref"),
            "data_range_start": projected_card_dict.get("data_range_start"),
            "data_range_end": projected_card_dict.get("data_range_end"),
            "missing_evidence_class": projected_card_dict.get("missing_evidence_class", []),
            "upgrade_requirements_ref": upgrade_req,
            "egress_receipt_ref": projected_card_dict.get("egress_receipt_ref")
        }
        
        payload = projected_card_dict.get("payload")
        if payload:
            pc_priv = {
                "timeline": payload.get("timeline"),
                "engineering_proof": payload.get("engineering_proof"),
                "observability": _safe_serialize(payload.get("observability", {})), 
                "evidence_refs": payload.get("evidence_refs", [])
            }
            eng_proof = payload.get("engineering_proof", {})
            pc_min.update(eng_proof)
        else:
            pc_priv = None
            
        bundle["pc_min"] = pc_min
        bundle["pc_priv"] = pc_priv
        
        return _safe_serialize(bundle)
