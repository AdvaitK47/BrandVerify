# BrandVerify — Automated Pre-Flight Brand Governance & Compliance Platform

> **Verify before you publish.** Intelligent, multi-modal pre-flight brand governance ensuring marketing copy, pitch decks, social graphics, podcasts, and commercial videos strictly comply with regulatory directives and custom brand rulebooks.

---

## 1. Executive Summary & Design Aesthetics

BrandVerify is engineered with a **modern high-contrast monochrome aesthetic**:
- **Canvas**: Clean, pitch-black surface (`#000000`) across all pages.
- **Palette**: Strictly black, grey, and white with zero blue tinting or visual noise.
- **Review Highlighting**: Muted, desaturated tones (soft green, soft red, soft gold) are strictly isolated to compliance diff review screens (`review.html`).
- **Icons**: Monotone stroke SVG line icons throughout (no emojis).
- **Typography**: Modern typography powered by *Plus Jakarta Sans* and *JetBrains Mono*.
- **User Avatar**: Newspaper-style high-contrast monochrome profile avatar.

---

## 2. Implemented Features

### A. Pre-Flight Content Ingestion & Routing (`frontend/index.html`)
- **Direct Multi-Modal Hub**: 5 dedicated content verification pathways:
  1. **Text**: Ad copy, headlines, social captions, and marketing taglines.
  2. **Docs**: Multi-page pitch decks, investor briefs, whitepapers, and DOCX files.
  3. **Image**: 4K print media, Instagram/LinkedIn posts, website banners, and vector assets.
  4. **Vid**: Commercial broadcasts, video reels, and social motion clips.
  5. **Audio**: Podcast sponsorships, voiceover dialogue, and radio spots.
- **One-Click Pre-Flight Routing**: Clicking any card routes directly into the active brand workspace with the corresponding checker subtab pre-selected.

### B. Enterprise Brand Profile Governance (`frontend/dashboard.html`)
- **Managed Brand Profiles**: Pre-seeded with multi-industry enterprise profiles:
  - *Acme Global Technologies* (Enterprise Cloud & SaaS)
  - *Luxe & Co. Haute Couture* (Luxury Fashion & Retail)
  - *Apex Financial Partners* (Asset Management & FinTech)
  - *Pulse BioHealth & Nutrition* (Clinical Biotechnology)
- **Minimalist Card Layout**: Clean card layout displaying initials avatar, company title, industry, and direct action triggers.
- **Dynamic Brand Management**:
  - Modal-based brand creation (`+ Add New Brand`) with custom rulebook configuration.
  - Confirmation modal for brand profile deletion.
  - Client-side persistence via `localStorage` with fallback seeds.

### C. Multi-Modal Compliance Checker Workspace (`frontend/brand.html`)
- **Monotone Subtab Interface**: Instant switching between Text, Document, Post & Image, Audio, and Video checkers with clean SVG line icons.
- **Universal Target Channels**: Standardized targets plus the **"Other Channel / Custom Target"** option across all upload panels.
- **Custom Upload Rule Enforcer**: Each upload checker features an optional custom rule prompt (`Specific Rule for this Upload (Optional)`), allowing users to enforce targeted, scan-specific constraints (e.g., *"Check if taste description exceeds 2 seconds"*, *"Ensure 18+ legal footer included"*).
- **Brand Context Switcher**: Dropdown in the header enables switching between active brand profiles without leaving the workspace.

### D. Side-by-Side Diff & Review Hub (`frontend/review.html`)
- **Split Visual Diff Engine**: Side-by-side view comparing original creative copy against the compliance-approved recommended version.
- **Interactive Flag Inspector**: Severity badges (*Critical*, *Warning*, *Info*) highlighting regulatory violations (unsubstantiated superlatives, missing safe-harbor footnotes, CIE2000 color distance violations).
- **One-Click Editorial Actions**:
  - *Accept All Recommendations* (instant approval and auto-commit)
  - *Manual Edit & Override*
  - *Download Compliance Report (.PDF)*
  - *Publish Approved Creative Asset*

### E. Authentication & Navigation Bar
- **Edge-to-Edge Navigation**: Flat, modern top bar with clean 3-tab navigation (*Overview*, *Dashboard*, *Compliance Checker*).
- **Guest State**: Only displays the *Log In* button (and hero *Get Started* button).
- **Logged-In State**: Displays the high-contrast newspaper B&W avatar with an interactive dropdown menu (Managed Brands, Compliance Workspace, Log Out).

---

## 3. Repository Architecture

The project is structured into clear, decoupled layers for frontend presentation and backend intelligence:

```
BrandVerify/
├── frontend/                     # Client application (Clean normal black UI)
│   ├── index.html                # Overview hub & 5-card ingestion triggers
│   ├── dashboard.html            # Managed brand profiles & dynamic brand modal
│   ├── brand.html                # Multi-modal compliance checker workspace
│   ├── submission.html           # Full campaign asset submission workflow
│   ├── review.html               # Side-by-side diff comparison & approval hub
│   ├── login.html                # Authentication entrypoint
│   ├── templates/                # Mirrored HTML templates for FastAPI Jinja2
│   └── static/
│       ├── css/
│       │   └── styles.css        # Core design system & monochrome tokens
│       ├── js/
│       │   └── app.js            # Brand manager, auth state, and mock API logic
│       └── images/
│           ├── BrandVerify.svg   # Monochrome logo vector
│           └── avatar_newspaper.jpg # High-contrast B&W profile avatar
│
├── backend/                      # Python backend & compliance engine
│   ├── main.py                   # FastAPI application & route mounting
│   ├── config.py                 # Pydantic Settings & environment variables
│   ├── requirements.txt          # Backend dependencies
│   ├── api/                      # REST API routers
│   │   ├── __init__.py           # Unified router aggregation
│   │   ├── brands.py             # CRUD endpoints for managed brands
│   │   ├── verify.py             # Pre-flight scan endpoints (text, doc, image, audio, video)
│   │   └── rules.py              # Rulebooks & regulatory policy endpoints
│   ├── services/                 # Compliance verification engines
│   │   ├── __init__.py
│   │   ├── text_verifier.py      # Claims, superlatives, and tone verifier
│   │   ├── image_verifier.py     # Delta-E color distance & logo margin calculator
│   │   ├── doc_verifier.py       # PDF/DOCX multi-page disclaimer parser
│   │   ├── audio_verifier.py     # Speech transcription & loudness auditor
│   │   └── video_verifier.py     # Scene transition & on-screen disclaimer scanner
│   ├── models/                   # Pydantic & SQLAlchemy domain models
│   │   ├── __init__.py
│   │   ├── brand.py              # Brand, Rulebook, and Asset schemas
│   │   └── scan.py               # ScanRequest, ComplianceFlag, and Diff schemas
│   └── tests/                    # Backend unit test suite
│       ├── __init__.py
│       └── test_verify.py        # Verification service assertions
│
├── run_demo.py                   # Zero-dependency local preview server
├── requirements.txt              # Complete project requirements & ML libraries
└── README.md                     # Platform documentation & engineering roadmap
```

---

## 4. Engineering Roadmap: Next Steps to Implement

For the backend, AI/ML, and DevOps engineers taking over the next development phase:

### 1. Multi-Modal LLM Claim Substantiation Engine
- **Integration**: Connect `backend/services/text_verifier.py` with OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet), or Gemini 1.5 Pro.
- **Rulebook RAG**: Index uploaded PDF guideline rulebooks using vector embeddings (e.g. pgvector or ChromaDB) to ground all claim evaluations in cited legal precedents.
- **Custom Rule Prompting**: Pipe the `custom_rule` input directly into the LLM system prompt as an overriding compliance constraint.

### 2. Computer Vision & Color Precision Pipeline
- **Delta-E Calculation**: Expand `backend/services/image_verifier.py` using `scikit-image` / `colormath` to convert RGB pixel values to CIE L\*a\*b\* and calculate exact CIE2000 color distance ($\Delta E_{00}$) against official hex swatches.
- **Logo Boundary Detection**: Implement YOLOv8 or OpenCV template matching to detect brand logo coordinates and measure exclusion zone padding in pixels.

### 3. Document & Legal Disclosure Extraction
- **PDF Extraction**: Implement `PyMuPDF` (`fitz`) and `pytesseract` OCR in `backend/services/doc_verifier.py` to extract multi-page headers, footers, and table footnotes.
- **Safe Harbor Matching**: Compare extracted footers against mandatory statutory disclosure templates (e.g. SEC Rule 10b-5, FDA disclaimer blocks).

### 4. Audio & Video Multi-Stream Auditing
- **Speech Transcription**: Integrate `openai-whisper` (or `faster-whisper`) in `backend/services/audio_verifier.py` to transcribe audio stems and detect spoken superlatives and claims.
- **Loudness Compliance**: Use `pyloudnorm` / `librosa` to verify ITU-R BS.1770 / EBU R128 integrated loudness (target $-24 \pm 1$ LUFS).
- **Scene Pacing & Disclaimer Frames**: Use `PySceneDetect` in `backend/services/video_verifier.py` to count scene transitions and verify that on-screen legal disclaimers persist for at least 3.0 continuous seconds.

### 5. Persistent Database & Async Processing
- **Database**: Connect PostgreSQL via SQLAlchemy with Alembic migrations for persistent audit records.
- **Async Queue**: Use Celery / Redis to handle asynchronous background processing for large 4K video reels and multi-page pitch decks.

---

## 5. Quickstart & Local Development

### Option A: Zero-Dependency Local Frontend Preview
To start the built-in preview server immediately (no extra dependencies required):
```bash
python run_demo.py
```
Open your browser at **`http://localhost:8000`**.

### Option B: Running the FastAPI Backend
To run the full FastAPI application with active REST endpoints:
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```
Interactive Swagger documentation will be available at:
- **`http://localhost:8000/docs`** (Swagger UI)
- **`http://localhost:8000/redoc`** (ReDoc)

### Running Backend Tests
```bash
pytest backend/tests/
```

---

## 6. License & Compliance
Proprietary & Confidential. Built for intelligent automated brand governance.