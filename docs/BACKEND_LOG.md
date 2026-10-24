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
