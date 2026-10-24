# BrandVerify Backend Change Log

Every change made while working through the backend with Claude's guidance.
Newest steps at the bottom. To see any change: git show <commit>.
To undo one safely: git revert <commit>.

## Tech stack followed
FastAPI, Pydantic v2, SQLAlchemy 2.0 (+ Alembic later), SQLite locally and
PostgreSQL later via DATABASE_URL, pytest, settings only via backend/config.py.

## Done

Step 1-2. Environment
  - Created venv/ and installed: fastapi, uvicorn, pydantic-settings,
    python-multipart, groq, pytest, httpx.
  - ROS is installed on this machine and breaks pytest. Always run tests as:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest backend/tests -v

Step 3. Tests (file: backend/tests/test_verify.py)
  - Old test expected flag_type "superlative" and invented numbers like "3.8X".
    Code now uses "claim_substantiation". Test rewritten. Result: 5 passed.

Step 4. Git (commit 260389b)
  - Home folder had an accidental empty git repo. Project got its own git init.
  - Branch renamed master -> main. venv/ added to .gitignore.

Step 5. Recommended copy fix (commit b01e3d7)
  - File: backend/services/text_verifier.py
  - Before: the risky phrase was REPLACED by advice text (garbled sentence).
  - After: original wording kept, "[REVIEW: <advice>]" added after each phrase.
  - Test added: test_recommended_text_keeps_original_wording.
  - Undo: git revert b01e3d7

Step 7. AI explainer made safe (commit d7f53be)
  - Files: backend/config.py (added GROQ_API_KEY setting),
    backend/services/ai_explainer.py (groq imported lazily, key read from
    settings, errors now logged with logger.exception).
  - Reason: a missing groq package used to crash the whole server at startup.
  - Undo: git revert d7f53be

Step 8-10. Groq key
  - GROQ_API_KEY stored in .env (git-ignored, never commit it).
  - Model qwen/qwen3.8-27b confirmed valid via the Groq models list.
  - AI explanation confirmed visible in the browser.

Step 12. Scan storage
  - File: backend/db.py (SQLAlchemy: init_db, save_scan, list_scans, get_scan).
  - Committed as "Add SQLAlchemy-based scan history storage".
  - Claude first suggested a plain-sqlite3 version, then replaced it because
    it did not match the project stack (SQLAlchemy + Alembic + PostgreSQL).
  - *.db added to .gitignore.
  - STATUS: file created and committed. Fake-scan test result NOT yet
    confirmed (expected: LIST has test-1, GET True, MISS None).
  - Undo: git revert <commit of "Add SQLAlchemy-based scan history storage">

## Next (not done yet)
  - Step 13: save every text scan in verify.py and add GET /api/v1/scans and
    GET /api/v1/scans/{scan_id}.
  - Then: set up Alembic before any table structure changes.
  - Then: real document verifier, then image, then audio and video.

## Open decisions for the team (Claude must not decide these alone)
  1. Sync or async SQLAlchemy? Currently sync, called safely from async routes.
  2. Which AI provider is official? Code uses Groq; config/README mention
     OpenAI, Anthropic, Gemini.

## Known issues owned by others
  - Frontend: flag boxes under the diff and the "68% score" card are hardcoded
    demo text, not driven by the backend "flags" list.
  - Frontend: AI explanation shows raw ** markdown symbols.
  - Backend: /verify/upload still returns mock results for image, document,
    audio and video, and marks info-only results as warnings_detected.

Step 12 CONFIRMED: fake-scan test passed (LIST had test-1, GET True, MISS None).

Step 13 DONE: scan history
  - New: backend/api/scans.py (GET /api/v1/scans, GET /api/v1/scans/{scan_id}).
  - Edited: backend/api/verify.py (text scans saved via run_in_threadpool;
    a save failure is logged and does not break the scan),
    backend/api/__init__.py (router registered), backend/models/scan.py
    (ScanSummary added), backend/main.py (init_db() at startup via lifespan).
  - Verified: browser scan (25) and curl scan (70) both listed via
    GET /api/v1/scans; a fresh Python process reads them from brandverify.db.
    6 tests pass.
  - Undo: git revert 2c033d0
  - NOT YET DONE: automated API tests (need a separate test database so
    tests do not write to brandverify.db). Only /verify/text saves scans;
    /verify/upload does not save yet (it still returns mock data).
  - Known: ai_explainer.explain_findings is a blocking call inside an async
    route (can hold up other requests for up to 20s). Fix later with
    run_in_threadpool.

Step 14 DONE: API tests for scan history
  - New: backend/tests/conftest.py (sets a temporary DATABASE_URL BEFORE any
    backend import; fixture "client" replaces the AI call with a fixed text).
  - New: backend/tests/test_api_scans.py (7 tests: throwaway-DB safety check,
    save + list, get by id, 404, filter by brand, empty text 400, limit 422).
  - Result: 13 tests pass. Real brandverify.db untouched.
  - Rule: conftest.py must stay free of any backend import above the
    DATABASE_URL line.
  - Undo: git revert <commit "Add API tests for scan history using a throwaway database">

Step 14 CONFIRMED: 13 passed, real brandverify.db untouched (2 scans).
  - Undo for step 14: git revert f46c2eb

Step 15 DONE: shared status rule
  - File: backend/api/verify.py. New function determine_overall_status(flags):
    "warnings_detected" if any flag is above info, else "compliant".
    Used by both /verify/text and /verify/upload.
  - Why: upload said "warnings_detected" for info-only results, text did not.
  - New: backend/tests/test_status.py (5 tests). 18 tests pass.
  - Open question for the team: should critical flags give "non_compliant"?
    The ScanResult model comments list that status but nothing produces it.
  - Undo: git revert <commit "Use one shared overall-status rule...">

Step 15 CONFIRMED: 18 tests pass.
  - Undo for step 15: git revert c356703

Step 16A DONE: document text extraction
  - New: backend/services/doc_extractor.py (extract_document: .pdf via
    PyMuPDF, .docx via python-docx incl. tables, headers and footers).
    Imports are lazy so a missing library cannot crash the server.
  - New: backend/tests/test_doc_extractor.py (5 tests, use temp files).
  - New dependency: python-docx>=1.1.0 added to requirements.txt and
    backend/requirements.txt (PyMuPDF added to backend/requirements.txt).
    TEAM: python-docx was not in the original requirements.
  - Not connected to any endpoint yet (that is part B).
  - Known limit: scanned PDFs have no text layer; extractor returns
    has_text = False. OCR (pytesseract, in the roadmap) is a later step.
  - If PyMuPDF is not installed locally, the 2 PDF tests are skipped.
    Install later: pip install --default-timeout=120 --retries 10 PyMuPDF
  - Undo: git revert <commit "Add document text extraction for PDF and DOCX">

## AGREED ESSENTIAL PLAN (README items parked for later)
  1. 16A document reader (done)
  2. 16B document upload: size/type limits, claim rules on the text, save to history
  3. 16C required-disclaimer check for documents
  4. Label simulated image/audio/video results honestly, do not save them
  5. Stop the AI call from blocking the server
  6. Per-brand rules from files so brand_id changes the checks
  7. Alembic migrations
  PARKED: real image/audio/video checks, OCR, Celery/Redis, PostgreSQL, auth.

Step 16B DONE: document upload scanning
  - Rewritten: backend/services/doc_verifier.py (was a mock). New
    verify_document(): extract text, run verify_text_compliance on it.
  - Edited: backend/api/verify.py. content_type=document now goes through
    _verify_document_upload(): extension check (400), streamed to a temp
    file with size limit (413), unreadable/empty -> 422, temp file always
    deleted, AI explanation, saved to history, returns a ScanResult.
  - Edited: backend/config.py (MAX_UPLOAD_MB = 25).
  - New: backend/tests/test_api_documents.py (6 tests).
  - Limits: each claim is flagged once per document (first match only);
    no page numbers yet; scanned PDFs rejected (OCR parked); documents
    have no diff pane (diff = None).
  - Frontend TODO (teammate): the Document tab still shows "not connected
    yet". Endpoint: POST /api/v1/verify/upload (multipart form: brand_id,
    content_type=document, title, target_channel, custom_rule, file).
  - Undo: git revert <commit "Scan uploaded DOCX/PDF documents...">

Step 16C DONE: required-disclaimer check for documents
  - New: backend/services/disclaimer_check.py. Each rule has a trigger
    pattern and an accepted-wording pattern; if the trigger is found and
    the wording is missing anywhere in the document (body, tables, headers,
    footers), a "missing_disclaimer" WARNING flag is raised.
  - Rules so far: forward-looking statements; past performance / results
    may vary (for investment-return language).
  - Edited: backend/services/doc_verifier.py (adds the disclaimer flags
    after the claim-rule flags).
  - New: backend/tests/test_disclaimer_check.py (6 tests) and
    backend/tests/test_api_disclaimers.py (3 tests). Total: 38 passed.
  - Limits: heuristic keyword rules, not legal determinations; the same
    two rules apply to every brand until per-brand rules (later step);
    checks the whole document, not whether the disclaimer sits near the
    claim; documents only, text scans do not run this check.
  - Undo: git revert <commit "Check uploaded documents for required disclaimers">

Step 17 DONE: simulated image/audio/video results are labelled, not saved
  - Why: image_verifier, audio_verifier and video_verifier do not analyse
    the file. They return fixed demo findings (the image one returned
    nothing, so every image looked "compliant" with 100).
  - Edited: backend/api/verify.py. Upload for image/audio/video now returns
    _simulated_response(): overall_status "simulated", compliance_score
    null, scan_id null, simulated true, saved false, a plain-language
    notice, and "[SIMULATED]" prefixed on every flag title.
    Never saved to history. Document and text scans are unchanged.
  - New: backend/tests/test_api_simulated.py (7 tests). Total: 45 passed.
  - Updated: backend/tests/test_status.py (old audio test expected
    "compliant"; now expects "simulated").
  - FRONTEND TODO (teammate): for content_type image/audio/video the
    response now has compliance_score = null and scan_id = null. Show the
    notice and a "Simulated" badge instead of a score, and do not link to
    a saved scan.
  - Real image/audio/video checks stay PARKED.
  - Undo: git revert <commit "Label simulated image/audio/video results...">

Step 18 DONE: AI call no longer blocks the server
  - Why: POST /verify/text called explain_findings() directly inside an
    async endpoint. That call is a network request (up to 20 s timeout),
    so while it waited, the whole server could not answer anyone else.
  - Edited: backend/api/verify.py. The text endpoint now runs
    explain_findings through run_in_threadpool. The document upload,
    save_scan and history endpoints already did.
  - New: backend/tests/test_ai_not_blocking.py (2 tests). A fake explainer
    records whether it ran on the event loop or in a worker thread, for
    both the text and document endpoints. Total: 47 passed.
  - Not changed: the verify_text_compliance rule check is fast regex and
    still runs inline. The AI call keeps its 20 s timeout and its fallback
    messages.
  - Undo: git revert <commit "Run the AI explanation call in a worker thread...">

Step 19 DONE: per-brand rules from files
  - Why: scans ignored brand_id. Every brand got the same hard-coded 4
    claim patterns and 2 disclaimer rules.
  - New: backend/rules/<brand_id>.json (default, acme-tech, luxe-fashion,
    apex-fin, pulse-health). Each file has "claims" (pattern, title, fix,
    severity) and "disclaimers" (trigger, accepted wording, title, fix).
    default.json equals the old hard-coded rules, so unknown brands
    behave exactly as before.
  - New: backend/services/brand_rules.py (load_rules, load_all_rule_files,
    RuleFileError) and backend/services/rule_models.py. brand_id is only a
    lookup key into existing files, never part of a file path. Files are
    read on every scan, so rule edits apply without a restart. A broken
    rule file raises RuleFileError (the scan fails loudly instead of
    using wrong rules).
  - Edited: text_verifier.py, disclaimer_check.py, doc_verifier.py,
    api/verify.py (rules chosen by brand_id).
  - New tests: test_brand_rules.py (12) and test_api_brand_rules.py (4).
    Total: 63 passed.
  - Limits: rules are heuristic keyword checks for human review, not
    legal advice; compliance should review the wording before real use.
    Disclaimer rules run on documents only, not on text scans. The brand
    rulebook summaries on the brand page still describe checks that do not
    exist yet (frontend text, teammate TODO).
  - Rule files: edit the JSON; run the tests afterwards, they validate
    every file and compile every pattern.
  - Undo: git revert the per-brand rules commits.

Step 20 DONE: PII masking before the AI call
  - Why: explain_findings() sent the ad copy and the findings to Groq (a
    hosted service) unmasked, which contradicted the submission's privacy
    promise.
  - New: backend/services/pii_masker.py (PiiMasker). Replaces email
    addresses, phone numbers, card numbers (any 13-19 digits), US SSNs,
    Indian PAN and Aadhaar-style IDs with tags like [EMAIL_1]. The real
    values stay on the server and are put back into the AI's answer
    locally.
  - Edited: backend/services/ai_explainer.py. The masking sits inside
    explain_findings(), the only place text leaves for the network, so
    text, document and any future scan type are covered. The ad copy,
    finding titles, descriptions, snippets, fixes and citations are all
    masked.
  - New tests: test_pii_masker.py (17) and test_ai_privacy.py (3). A fake
    AI service records what it receives; the tests check no email/phone
    is in it, the answer is restored, and a clean scan makes no AI call.
    Total: 83 passed.
  - NOT DONE (be honest in the demo/submission): people's names, places
    and codenames are NOT masked. Microsoft Presidio (named in the
    submission) needs a spaCy model and is a later step. Either add
    Presidio, or word the submission as "emails, phone numbers and IDs".
  - Other limits: pattern-based, so unusual formats can be missed; the AI
    is still a hosted Groq model, not a local Llama/Mistral as the
    submission describes.
  - Undo: git revert <commit "Mask personal details before text is sent...">

Step 21 DONE: approve/reject decisions with a permanent audit log
  - Why: the submission promises human approval and "immutable decision
    logs". Before this, a scan could be saved but nobody could approve or
    reject it.
  - New table audit_log (db.py: AuditRecord). Created automatically at
    startup by init_db (create_all); the existing scans table is untouched.
    No Alembic migration exists yet.
  - New endpoints (api/scans.py):
      POST /api/v1/scans/{scan_id}/decision   body: decision
        ("approved" | "rejected"), reviewer, comment. Rejecting needs a
        comment. Approving a scan with a critical flag needs a comment and
        is recorded with overrode_critical = true. Unknown scan: 404.
      GET  /api/v1/scans/{scan_id}/audit      every decision, oldest first.
  - review_status ("pending_review", "approved", "rejected") added to
    ScanResult and ScanSummary; the latest decision is the current status.
    Scan history and scan detail fill it in.
  - Immutable: the app can only add audit rows. An update or delete of an
    AuditRecord raises AuditLogError (SQLAlchemy event guard), tested.
    LIMIT: this is application-level only. Someone with direct database
    access can still edit rows. Real protection needs PostgreSQL triggers
    or permissions (later).
  - LIMIT: no login yet, so the reviewer name is typed in and NOT
    verified, and "creators cannot approve their own content" is not
    enforced. Both need JWT login and roles (later).
  - New: backend/models/audit.py, backend/tests/test_api_review.py
    (10 tests). Total: 93 passed.
  - Frontend TODO (teammate): connect review.html to the decision and audit
    endpoints; show review_status on the dashboard and history. Scan
    responses now include a review_status field.
  - Undo: git revert <commit "Add approve/reject decisions with a
    permanent audit log">. The audit_log table stays in the database file.

Step 22 DONE: PDF audit report generator (WeasyPrint)
Why: human reviewers and legal teams need downloadable, immutable PDF audit 
     trails for compliance and archiving.
New service (backend/services/pdf_report.py):
     Uses WeasyPrint to dynamically build PDF documents containing scan metadata, 
     flagged findings, and full immutable audit history.
New endpoint (backend/api/scans.py):
     GET /api/v1/scans/{scan_id}/report.pdf - returns application/pdf file.
Dependencies: WeasyPrint (Python) + system Pango libraries (libpango-1.0-0, libpangoft2-1.0-0).
