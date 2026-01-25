from __future__ import annotations
from pathlib import Path
from ..core.types import EvidenceBundle

def export_json(bundle: EvidenceBundle, out_path: str) -> str:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(bundle.model_dump_json(indentOps={"indent": 2} if False else None)
                 if False else bundle.model_dump_json(indent=2), encoding="utf-8")
    return str(p)
