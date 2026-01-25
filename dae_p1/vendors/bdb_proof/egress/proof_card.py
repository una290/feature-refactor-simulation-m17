from __future__ import annotations
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from ..core.types import EvidenceBundle

def export_proof_card_pdf(bundle: EvidenceBundle, out_path: str) -> str:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(p), pagesize=letter)
    width, height = letter
    x = 40
    y = height - 40

    def line(txt, dy=14):
        nonlocal y
        c.drawString(x, y, txt)
        y -= dy

    line("DAE_Proof — Proof Card (Closure-Ready)")
    line(f"Evidence ID: {bundle.evidence_id}")
    line(f"Case ID: {bundle.case.case_id}    Device ID: {bundle.case.device_id}")
    line(f"Window: {bundle.window_ref.window_id}  ({bundle.window_ref.start_ts.isoformat()} — {bundle.window_ref.end_ts.isoformat()})")
    line("")

    line(f"Triage: {bundle.triage.label} (confidence: {bundle.triage.confidence})")
    line(f"Admission Verdict (BDB): {bundle.admission_verdict}")
    line(f"Recognition Verdict: {bundle.recognition.recognition_verdict}  (operative_state: {bundle.recognition.operative_state})")
    line(f"Boundary Severity: {bundle.boundary_eval.max_severity}")
    line(f"FP Lite Regime: {bundle.fp_lite.regime_code}  ({bundle.fp_lite.fp_lite_version})")
    line(f"Readiness: {bundle.readiness.readiness}")
    if bundle.readiness.missing_fields:
        line(f"Missing fields: {', '.join(bundle.readiness.missing_fields)}")
    line("")

    line("Reason Codes:")
    for rc in bundle.reason_codes[:20]:
        line(f"  - {rc}")
    if len(bundle.reason_codes) > 20:
        line(f"  ... ({len(bundle.reason_codes)-20} more)")

    line("")
    line("Snapshots:")
    line(f"  policy_snapshot_ref: {bundle.snapshot_refs.policy_snapshot_ref}")
    line(f"  version_ref: {bundle.snapshot_refs.version_ref}")
    line(f"  basis_ref: {bundle.snapshot_refs.basis_ref}")

    if bundle.counterforce:
        line("")
        line("Counterforce (Conservative Braking):")
        line(f"  action: {bundle.counterforce.action}")
        line(f"  constraint_delta_ref: {bundle.counterforce.constraint_delta_ref}")
        if bundle.counterforce.cooldown_seconds:
            line(f"  cooldown_seconds: {bundle.counterforce.cooldown_seconds}")

    c.showPage()
    c.save()
    return str(p)
