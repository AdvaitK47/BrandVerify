import json, re
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from backend.services.rulebook_parser import extract_rulebook_text, draft_rules_from_text
from backend.services.compliance_checker import check_text, check_colors, overall_status

router = APIRouter(tags=["Rulebook and Compliance"])
DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "brand_rules"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MAX_BYTES = 12 * 1024 * 1024

def _safe_id(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]", "_", value.strip())
    if not value or value in {".", ".."}: raise HTTPException(400, "Invalid brand_id.")
    return value

def load_rules(brand_id: str) -> dict:
    path = DATA_DIR / f"{_safe_id(brand_id)}.json"
    if not path.exists(): raise HTTPException(404, f"No saved rules for brand '{brand_id}'.")
    try: return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError: raise HTTPException(500, "Saved rules JSON is invalid.")

class ApproveRules(BaseModel):
    approved_colors: list[str] = Field(default_factory=list)
    required_phrases: list[str] = Field(default_factory=list)
    prohibited_phrases: list[str] = Field(default_factory=list)
    generic_rules_for_human_review: list[str] = Field(default_factory=list)

class TextCheck(BaseModel):
    brand_id: str
    text: str

@router.post("/api/rulebooks/upload")
async def upload_rulebook(brand_id: str = Form(...), file: UploadFile = File(...)):
    filename = file.filename or "rulebook"
    ext = Path(filename).suffix.lower()
    if ext not in {".pdf", ".docx", ".txt"}: raise HTTPException(400, "Upload PDF, DOCX or TXT.")
    raw = await file.read()
    if len(raw) > MAX_BYTES: raise HTTPException(413, "Rulebook must be 12 MB or smaller.")
    temp = DATA_DIR / f"temp_{uuid4().hex}{ext}"
    try:
        temp.write_bytes(raw)
        text = extract_rulebook_text(str(temp))
        if not text.strip(): raise HTTPException(422, "No readable text. Scanned PDFs need OCR.")
        draft = draft_rules_from_text(text, _safe_id(brand_id), filename)
        return {"message": "Review the draft and approve it before scanning.", "rules": draft}
    except HTTPException: raise
    except Exception as exc: raise HTTPException(400, f"Could not parse rulebook: {exc}")
    finally: temp.unlink(missing_ok=True)

@router.post("/api/rulebooks/{brand_id}/approve")
def approve_rulebook(brand_id: str, body: ApproveRules):
    colors = []
    for color in body.approved_colors:
        color = color.strip().upper()
        if not re.fullmatch(r"#[0-9A-F]{6}", color): raise HTTPException(422, f"Invalid HEX color: {color}")
        colors.append(color)
    rules = {"brand_id": _safe_id(brand_id), "approved_colors": list(dict.fromkeys(colors)),
        "required_phrases": [x.strip() for x in body.required_phrases if x.strip()],
        "prohibited_phrases": [x.strip() for x in body.prohibited_phrases if x.strip()],
        "generic_rules_for_human_review": [x.strip() for x in body.generic_rules_for_human_review if x.strip()],
        "approved": True}
    (DATA_DIR / f"{_safe_id(brand_id)}.json").write_text(json.dumps(rules, indent=2), encoding="utf-8")
    return {"message": "Reviewed rules saved.", "rules": rules}

@router.get("/api/rulebooks/{brand_id}")
def get_rulebook(brand_id: str):
    return load_rules(brand_id)

@router.post("/api/compliance/text")
def text_compliance(body: TextCheck):
    rules = load_rules(body.brand_id)
    if not rules.get("approved"): raise HTTPException(409, "Admin must approve rules before scanning.")
    findings = check_text(body.text, rules)
    return {"brand_id": body.brand_id, "media_type": "text", "status": overall_status(findings),
        "findings": findings, "note": "Exact phrases/basic privacy patterns only; semantic factual checks need AI and human review."}

@router.post("/api/compliance/colors")
def color_compliance(brand_id: str = Form(...), colors_json: str = Form(...)):
    rules = load_rules(brand_id)
    if not rules.get("approved"): raise HTTPException(409, "Admin must approve rules before scanning.")
    try: colors = json.loads(colors_json)
    except json.JSONDecodeError: raise HTTPException(422, "colors_json must be a JSON array.")
    if not isinstance(colors, list) or not all(isinstance(c, str) for c in colors):
        raise HTTPException(422, "colors_json must be a JSON array of strings.")
    findings = check_colors(colors, rules)
    return {"brand_id": brand_id, "media_type": "image_colors", "status": overall_status(findings), "findings": findings}
