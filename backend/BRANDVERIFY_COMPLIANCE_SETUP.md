# BrandVerify compliance additions (MVP)

## Adds
- Upload a PDF/DOCX/TXT rulebook and extract text.
- Draft rules from HEX colors and clearly labelled lines (`Required phrase:`, `Required disclaimer:`, `Must include:`, `Prohibited phrase:`, `Banned phrase:`, `Must not say:`).
- Admin-approved rules saved as JSON by brand ID.
- Text checks: exact required/prohibited phrases and basic email/phone pattern flags.
- Audio: speech transcription via faster-whisper then same checks.
- Video: FFmpeg audio extraction, transcription, and rough sampled-frame color signals.

This is an MVP. It does not reliably interpret every natural-language rulebook, prove factual claims, match logos, run OCR on video frames, or check music licensing/BPM. Admin review is required.

## 1. Merge files
Copy the supplied `backend/` files into the existing project. Do not replace your existing backend files.

## 2. Install Python packages
Run in the same environment used to run FastAPI:
```bash
pip install pymupdf python-docx opencv-python faster-whisper python-multipart
```
Video requires FFmpeg installed separately and added to PATH. Check with `ffmpeg -version`.

## 3. Register new routers in backend/main.py
Keep your existing `app = FastAPI()`, CORS and current routers. Add:
```python
from backend.api.rulebook_compliance import router as rulebook_compliance_router
from backend.api.media_compliance import router as media_compliance_router
```
After `app = FastAPI()` register:
```python
app.include_router(rulebook_compliance_router)
app.include_router(media_compliance_router)
```
Do not include either router twice. These do not replace `/api/images/scan`. If your current media router already has the same paths, resolve duplicate routes before registering.

## 4. Start server
From the folder containing `backend/`:
```bash
python -m uvicorn backend.main:app --reload
```
Open `http://127.0.0.1:8000/docs`.

## 5. Test rulebook upload
Create `sample_rulebook.txt`:
```text
Approved colors: #173B67, #FFFFFF, #F4A261
Required phrase: Results may vary.
Prohibited phrase: 100% cure
Prohibited phrase: guaranteed health results
Tone: friendly and professional
Do not publish customer phone numbers or email addresses.
```
Use POST `/api/rulebooks/upload` with multipart form fields `brand_id=brand_demo` and `file=sample_rulebook.txt`. Inspect the draft response.

## 6. Approve rules
POST `/api/rulebooks/brand_demo/approve` with JSON:
```json
{
  "approved_colors": ["#173B67", "#FFFFFF", "#F4A261"],
  "required_phrases": ["Results may vary."],
  "prohibited_phrases": ["100% cure", "guaranteed health results"],
  "generic_rules_for_human_review": ["Tone: friendly and professional", "Do not publish customer phone numbers or email addresses."]
}
```
Only submit rules that an Admin has reviewed. The demo approval endpoint currently has no authentication; add Admin authorization before deployment.

## 7. Test text
POST `/api/compliance/text`:
```json
{"brand_id":"brand_demo","text":"Our product guarantees health results!"}
```

## 8. Test audio and video in Swagger
- POST `/api/compliance/audio`: multipart `brand_id=brand_demo`, `file=<audio>`.
- POST `/api/compliance/video`: multipart `brand_id=brand_demo`, `file=<video>`.
The first faster-whisper run may download its model and take time. Set `BRANDVERIFY_WHISPER_MODEL=tiny` for a smaller model. Video additionally requires FFmpeg.

## 9. Frontend FormData example
```javascript
const form = new FormData();
form.append("brand_id", selectedBrandId);
form.append("file", selectedFile);
const response = await fetch("http://127.0.0.1:8000/api/compliance/audio", {
  method: "POST", body: form
});
const data = await response.json();
if (!response.ok) throw new Error(data.detail || "Scan failed");
```
Do not manually set the multipart `Content-Type` header. Use the same pattern for rulebook upload and video.

For text:
```javascript
const response = await fetch("http://127.0.0.1:8000/api/compliance/text", {
  method: "POST",
  headers: {"Content-Type":"application/json"},
  body: JSON.stringify({brand_id: selectedBrandId, text: caption})
});
```

## Limitations before production
- JSON files are MVP storage, not PostgreSQL. Move to your database for concurrent users.
- Add authentication/RBAC, tenant isolation, file validation, audit logs, and background jobs.
- Add OCR for scanned PDFs and video frames; integrate the existing image scanner for image OCR/palette.
- Add semantic claim/tone checking against approved sources and route uncertain results to human review.
