"""BrandVerify app: API routers + the frontend, served from one origin."""

import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api import router as api_router               # image + media + text scans
from backend.api.rulebook_compliance import router as rulebook_router
from backend.api.media_compliance import router as media_compliance_router
from backend.api.rules import router as rules_router
from backend.api.media_scan import router as media_scan_router


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"

app = FastAPI(title="BrandVerify")
app.include_router(media_scan_router)
# Only needed if you open the pages from another origin (e.g. VS Code Live Server).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Development aid: return the real error text instead of a bare "Internal Server Error".
@app.exception_handler(Exception)
async def show_errors(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})


# 1. API routes first...
app.include_router(api_router)
app.include_router(rulebook_router)
app.include_router(media_compliance_router)
app.include_router(rules_router)

# 2. ...then the frontend LAST. A mount at "/" matches every path, so anything
#    registered after it would never be reached. Serves brand.html, static/css, static/js, etc.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
