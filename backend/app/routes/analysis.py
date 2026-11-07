import json, os, uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Analysis
from ..auth import get_current_user
from ..services.extractor import extract_text
from ..services.analyzer import analyze, TYPE_LABELS
from ..services.report import create_report

router = APIRouter(prefix="/api", tags=["analysis"])
BASE = Path(__file__).resolve().parents[2]
STORAGE_DIR = Path(os.getenv("TRUSTSHIELD_STORAGE_DIR", str(BASE))).expanduser().resolve()
UPLOAD_DIR = STORAGE_DIR / "uploads"; REPORT_DIR = STORAGE_DIR / "reports"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True); REPORT_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = 15 * 1024 * 1024
ALLOWED = {".pdf",".docx",".txt",".csv",".md",".png",".jpg",".jpeg",".tif",".tiff",".bmp"}

def serialize(a, include_text=True):
    return {"id":a.id,"filename":a.filename,"document_type":a.document_type,"score":a.score,"risk_level":a.risk_level,"confidence":a.confidence,"issues_count":a.issues_count,"findings":json.loads(a.findings_json or "[]"),"recommendations":json.loads(a.recommendations_json or "[]"),"extracted_text":(a.extracted_text or "") if include_text else "","created_at":a.created_at.isoformat() + "Z","report_url":f"/api/analysis/{a.id}/report"}

@router.post("/analyze")
async def analyze_file(file: UploadFile = File(...), document_type: str = Form(...), user=Depends(get_current_user), db: Session = Depends(get_db)):
    if document_type not in TYPE_LABELS: raise HTTPException(400, "Unsupported document type")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED: raise HTTPException(400, "Unsupported file type")
    safe_name = f"{uuid.uuid4().hex}{ext}"
    path = UPLOAD_DIR / safe_name
    content = await file.read(MAX_BYTES + 1)
    if not content: raise HTTPException(400, "The uploaded file is empty.")
    if len(content) > MAX_BYTES: raise HTTPException(413, "File too large. Maximum is 15 MB.")
    try:
        path.write_bytes(content)
    except OSError as exc:
        raise HTTPException(500, "Could not store the uploaded document. Check storage configuration.") from exc
    try:
        text, warnings = await run_in_threadpool(extract_text, str(path))
    finally:
        # The text is saved in the database; do not keep the raw upload (privacy + disk space).
        path.unlink(missing_ok=True)
    score, risk, confidence, findings, recommendations = analyze(text, document_type, file.filename, warnings)
    a = Analysis(user_id=user.id, filename=Path(file.filename or "document"+ext).name[:255], document_type=TYPE_LABELS[document_type], score=score, risk_level=risk, confidence=confidence, issues_count=sum(1 for f in findings if f.get('severity') in {'high','medium'}), extracted_text=text[:100000], findings_json=json.dumps(findings), recommendations_json=json.dumps(recommendations))
    db.add(a); db.commit(); db.refresh(a)
    return serialize(a)

@router.get("/history")
def history(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Analysis).filter(Analysis.user_id == user.id).order_by(Analysis.created_at.desc()).limit(100).all()
    return [serialize(x, include_text=False) for x in rows]

@router.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user.id).first()
    if not a: raise HTTPException(404, "Analysis not found")
    return serialize(a)

@router.delete("/analysis/{analysis_id}")
def delete_analysis(analysis_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user.id).first()
    if not a: raise HTTPException(404, "Analysis not found")
    (REPORT_DIR / f"trustshield_report_{a.id}.pdf").unlink(missing_ok=True)
    db.delete(a); db.commit()
    return {"message": "Deleted"}

@router.get("/analysis/{analysis_id}/report")
def report(analysis_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.user_id == user.id).first()
    if not a: raise HTTPException(404, "Analysis not found")
    p = create_report(a, user.name, REPORT_DIR)
    return FileResponse(p, media_type="application/pdf", filename=p.name)
