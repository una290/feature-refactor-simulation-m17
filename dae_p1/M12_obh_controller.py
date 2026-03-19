
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from .M00_common import EpisodeRecognition, iso, ProofCard, asdict
from .M10_timeline_builder import TimelineBuilder
from .M11_bundle_exporter import BundleExporter
from .M22_privacy_governance import PrivacyGovernance, BYUSE_RULES

# Contexts that are allowed to receive pc_priv (must exist in BYUSE_RULES)
_PRIV_CONTEXTS = set(BYUSE_RULES.keys())  # e.g. {"SUPPORT_CLOSURE", "DISPUTE", "COMPLIANCE_AUDIT"}
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

        # [REFERENCE-ONLY STORAGE DECOUPLING]
        # Tier 1: Public Ledger (Metadata Only)
        self.ledger_path = os.path.join(os.path.dirname(__file__), '..', 'brel_ledger.pkl')
        # Tier 2: Evidence Vault (Sensitive Payloads)
        self.vault_path = os.path.join(os.path.dirname(__file__), '..', 'evidence_vault.pkl')
        
        self.ledger: Dict[str, ProofCard] = {}
        self.vault: Dict[str, Dict[str, Any]] = {}

        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, 'rb') as f:
                    self.ledger = pickle.load(f)
            except Exception as e:
                print(f"[DEBUG M12] Failed to load ledger: {e}")

        if os.path.exists(self.vault_path):
            try:
                with open(self.vault_path, 'rb') as f:
                    self.vault = pickle.load(f)
            except Exception as e:
                print(f"[DEBUG M12] Failed to load vault: {e}")
                
        self.signed_manifests: set = set()
        self.disputed_episodes: set = set()

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
            
        # [STORAGE SPLIT] Save Card Metadata to Ledger, Payload to Vault
        evidence_payload = full_card.payload
        full_card.payload = None # Detach for Ledger
        
        self.ledger[recognition.episode_id] = full_card
        self.vault[recognition.episode_id] = evidence_payload
        
        print(f"[DEBUG M12] Saved episode '{recognition.episode_id}' to Decoupled Ledger/Vault.")
        try:
            with open(self.ledger_path, 'wb') as f:
                pickle.dump(self.ledger, f)
            with open(self.vault_path, 'wb') as f:
                pickle.dump(self.vault, f)
        except Exception as e:
            print(f"[DEBUG M12] Failed to persist storage: {e}")
            
        # 2. Pipeline: View Projector (Hook 2: Egress Filter)
        # Decide what actually leaves
        projected_card_dict = self.governance.project_view(full_card, authority_scope_ref)
        
        # 3. Pipeline: BYUSE Validator (Hook 3: Compliance Check)
        is_signed = recognition.episode_id in self.signed_manifests
        evidence_grade, upgrade_req = self.governance.evaluate_closure_grade(projected_card_dict, byuse_context_ref, is_signed=is_signed)

        # [產品化簡化] 判定是否需要剝離 Payload
        # 只要 grade 不是 "READY"，就不允許輸出 pc_priv
        should_strip = (evidence_grade != "READY")

        # We use the evidence_payload cached before Ledger detach
        payload = evidence_payload

        # Extract/Embed Logic based on Privacy
        # Assembling PC-Min (Always Safe / External View)
        pc_min = {
            "status": projected_card_dict.get("status"),
            "diagnosis_code": projected_card_dict.get("diagnosis_code"),
            "evidence_grade": evidence_grade,
            "episode_id": projected_card_dict.get("episode_id"),
            "window_ref": projected_card_dict.get("window_ref"),
            "data_range_start": projected_card_dict.get("data_range_start"),
            "data_range_end": projected_card_dict.get("data_range_end"),
            "missing_evidence_class": projected_card_dict.get("missing_evidence_class", []),
            "upgrade_requirements_ref": upgrade_req,
            "egress_receipt_ref": projected_card_dict.get("egress_receipt_ref")
        }
        
        if payload and not should_strip:
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
            if payload:
                # Still merge engineering_proof to pc_min even if stripped
                eng_proof = payload.get("engineering_proof", {})
                pc_min.update(eng_proof)

        # [OPTION 1 FIX] ALWAYS strip payload from the generic proof_card to avoid duplication!
        projected_card_dict["payload"] = None

        # 4. Assemble Final Bundle Dict
        bundle = {
            "spec": "DAE_P1_Priv_v2_CapabilityBased",
            "proof_card": _safe_serialize(projected_card_dict),
            "evidence_grade": evidence_grade,
            "upgrade_requirements_ref": upgrade_req,
            "pc_min": pc_min,
            "pc_priv": pc_priv
        }
        
        path = self.exporter.export(out_dir, recognition.episode_id, bundle)
        
        # [NEW] Audit Logging Persistence
        # [FIX-3] policy_snapshot_ref: refs['policy'] 現在是字串 Token，不是物件，直接讀取
        policy_ref_val = projected_card_dict.get("refs", {}).get("policy", "UNKNOWN")
        if isinstance(policy_ref_val, dict):
            policy_ref_val = policy_ref_val.get("policy_id", "UNKNOWN")
        self.audit_logger.log_egress(
            episode_id=recognition.episode_id,
            authority_scope_ref=authority_scope_ref,
            egress_receipt_ref=projected_card_dict.get("egress_receipt_ref"),
            policy_snapshot_ref=policy_ref_val,
            context_ref=byuse_context_ref,
            evidence_grade=evidence_grade
        )

        # Safe serialize
        safe_bundle = _safe_serialize(bundle)
            
        res = OBHResult(episode_id=recognition.episode_id, exported_path=path, bundle_content=safe_bundle)
        self.last_result = res
        return res

    def retrieve_bundle(self, episode_id: str, byuse_context_ref: Optional[str] = None, authority_scope_ref: Optional[str] = None, fields: Optional[str] = None):
        """Dynamically retrieve and re-project an existing proof card."""
        from dataclasses import asdict
        from .M12_obh_controller import _safe_serialize
        
        print(f"[DEBUG M12] Request to retrieve episode: '{episode_id}' from split storage")
        
        ref_card = self.ledger.get(episode_id)
        if not ref_card:
            print(f"[DEBUG M12] Episode '{episode_id}' not found in Ledger.")
            return None
            
        # Re-attach payload from Vault for projection logic (ephemeral join)
        ref_card.payload = self.vault.get(episode_id)
            
        projected_card_dict = self.governance.project_view(ref_card, authority_scope_ref)
        
        is_signed = episode_id in self.signed_manifests
        evidence_grade, upgrade_req = self.governance.evaluate_closure_grade(projected_card_dict, byuse_context_ref, is_signed=is_signed)

        # [產品化簡化] 判定是否需要剝離 Payload
        should_strip = (evidence_grade != "READY")
        if fields == "pc_min":
            should_strip = True
            
        # We need the payload to build pc_priv if it wasn't stripped
        payload = projected_card_dict.get("payload")
        # [FIX-3] 不再在這裡清空 egress_receipt_ref（那是 M22 project_view 的職責，不是 M12 的）

        pc_min = {
            "status": projected_card_dict.get("status"),
            "diagnosis_code": projected_card_dict.get("diagnosis_code"),
            "evidence_grade": evidence_grade,
            "episode_id": projected_card_dict.get("episode_id"),
            "window_ref": projected_card_dict.get("window_ref"),
            "data_range_start": projected_card_dict.get("data_range_start"),
            "data_range_end": projected_card_dict.get("data_range_end"),
            "missing_evidence_class": projected_card_dict.get("missing_evidence_class", []),
            "upgrade_requirements_ref": upgrade_req,
            "egress_receipt_ref": projected_card_dict.get("egress_receipt_ref")
        }
        
        if payload and not should_strip:
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
            if payload:
                eng_proof = payload.get("engineering_proof", {})
                pc_min.update(eng_proof)

        # [OPTION 1 FIX] ALWAYS strip payload from the generic proof_card to avoid duplication!
        projected_card_dict["payload"] = None

        bundle = {
            "spec": "DAE_P1_Priv_v2_CapabilityBased",
            "proof_card": _safe_serialize(projected_card_dict),
            "evidence_grade": evidence_grade,
            "upgrade_requirements_ref": upgrade_req,
            "pc_min": pc_min,
            "pc_priv": pc_priv
        }
        
        return _safe_serialize(bundle)
