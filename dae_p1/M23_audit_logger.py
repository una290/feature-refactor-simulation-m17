import json
import os
import time
from typing import Optional, Dict, Any

class AuditLogger:
    """
    M23 Audit Logger
    Persistent storage for privacy and access events.
    """
    def __init__(self, log_path: str = "audit_trail.jsonl"):
        self.log_path = log_path

    def log_egress(self, 
                   episode_id: str, 
                   authority_scope_ref: Optional[str], 
                   egress_receipt_ref: Optional[str],
                   policy_snapshot_ref: str,
                   context_ref: Optional[str],
                   evidence_grade: str) -> None:
        """
        Record the access attempt and whether sensitive payload was handed out.
        """
        entry = {
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "episode_id": episode_id,
            "authority_scope_ref": authority_scope_ref or "ANONYMOUS",
            "egress_receipt_ref": egress_receipt_ref,
            "policy_snapshot_ref": policy_snapshot_ref,
            "byuse_context": context_ref or "DEFAULT",
            "granted_evidence_grade": evidence_grade,
            "payload_exposed": egress_receipt_ref is not None
        }
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Failed to write audit log: {e}")
