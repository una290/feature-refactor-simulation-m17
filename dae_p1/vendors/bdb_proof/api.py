from __future__ import annotations
import datetime as dt
from pathlib import Path
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from .core.windowing import WindowManager
from .core.aggregator import WindowAggregator
from .core.boundary import BoundaryEngine
from .core.admission import AdmissionGate
from .core.evidence_store import EvidenceStore
from .core.recognition_store import RecognitionJournalStore
from .core.types import AdmissionRequest
from .ingress.base import RawIngest
from .ingress.fwa import FWAIngressAdapter
from .ingress.wifi import WiFiIngressAdapter
from .ingress.thermal import ThermalIngressAdapter
from .egress.ticket import to_ticket_fields
from .egress.csr_view import to_csr_view
from .egress.proof_card import export_proof_card_pdf

app = FastAPI(title="BDB Proof Reference API", version="0.1")

ROOT = Path(__file__).resolve().parent
POLICY = yaml.safe_load((ROOT / "configs" / "default_policy.yaml").read_text(encoding="utf-8"))

wm = WindowManager(window_seconds=300)
agg = WindowAggregator(wm)
bengine = BoundaryEngine(POLICY)
gate = AdmissionGate(POLICY, wm, agg, bengine)

store = EvidenceStore(str(Path("out") / "evidence.db"))
journal = RecognitionJournalStore(
    str(Path("out") / "recognition_journal.db"),
    retention_days=int(POLICY.get("retention", {}).get("journal_days", 7)),
)
OUTDIR = Path("out")
OUTDIR.mkdir(exist_ok=True)

adapters = {
    "fwa": FWAIngressAdapter(),
    "wifi": WiFiIngressAdapter(),
    "thermal": ThermalIngressAdapter(),
}

@app.post("/ingest/{domain}")
def ingest(domain: str, raw: RawIngest):
    if domain not in adapters:
        raise HTTPException(status_code=400, detail=f"unknown domain {domain}")
    obs = adapters[domain].normalize(raw)
    wref = agg.add(obs)
    return {"ok": True, "obs_id": obs.obs_id, "window_id": wref.window_id}

@app.post("/admit")
def admit(req: AdmissionRequest, window_id: str):
    bundle = gate.decide(req, window_id=window_id)
    store.put(bundle)
    journal.put(bundle)

    # export proof card pdf for convenience
    pdf_path = OUTDIR / f"{req.case.case_id}_proofcard.pdf"
    export_proof_card_pdf(bundle, str(pdf_path))

    return JSONResponse({
        "case_id": req.case.case_id,
        "evidence_id": bundle.evidence_id,
        "admission_verdict": bundle.admission_verdict,
        "recognition": bundle.recognition.model_dump(),
        "fp_lite": bundle.fp_lite.model_dump(),
        "triage": bundle.triage.model_dump(),
        "boundary_severity": bundle.boundary_eval.max_severity,
        "readiness": bundle.readiness.model_dump(),
        "ticket_fields": to_ticket_fields(bundle),
        "csr_view": to_csr_view(bundle),
        "device_health_latest": f"/devices/{req.case.device_id}/health/latest",
        "device_timeline": f"/devices/{req.case.device_id}/timeline?days=7",
        "proofcard_pdf": f"/cases/{req.case.case_id}/proofcard.pdf",
        "bundle_json": f"/cases/{req.case.case_id}/bundle",
    })


@app.get("/devices/{device_id}/health/latest")
def device_health_latest(device_id: str):
    latest = journal.get_latest(device_id)
    if not latest:
        raise HTTPException(status_code=404, detail="device not found")
    return JSONResponse(latest)


@app.get("/devices/{device_id}/timeline")
def device_timeline(device_id: str, days: int = 7, limit_events: int = 200):
    return JSONResponse(journal.timeline(device_id, days=days, limit_events=limit_events))

@app.get("/cases/{case_id}/bundle")
def get_bundle(case_id: str):
    bundle = store.get_latest_for_case(case_id)
    if not bundle:
        raise HTTPException(status_code=404, detail="case not found")
    return JSONResponse(bundle.model_dump())

@app.get("/cases/{case_id}/proofcard.pdf")
def get_proofcard(case_id: str):
    pdf_path = OUTDIR / f"{case_id}_proofcard.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="proofcard not found")
    return FileResponse(str(pdf_path), media_type="application/pdf", filename=pdf_path.name)

@app.get("/cases")
def list_cases():
    return {"cases": store.list_case_ids()}


@app.get("/schemas/{name}")
def get_schema(name: str):
    schema_path = ROOT / "configs" / "schemas" / name
    if not schema_path.exists():
        raise HTTPException(status_code=404, detail="schema not found")
    return JSONResponse(yaml.safe_load(schema_path.read_text(encoding="utf-8")) if name.endswith(".yaml") else __import__("json").loads(schema_path.read_text(encoding="utf-8")))

@app.get("/reason-codes")
def get_reason_codes():
    p = ROOT / "configs" / "reason_code_dictionary.json"
    return JSONResponse(__import__("json").loads(p.read_text(encoding="utf-8")))
