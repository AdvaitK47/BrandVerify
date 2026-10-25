"""
BrandVerify Application Entrypoint
Integrates Core Brand Governance, Scan History & Audit Logs,
and Real Multi-Modal (Image, Video, Audio, OCR, Rulebook) Compliance Scanners.
"""

from contextlib import asynccontextmanager
from pathlib import Path
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.db import init_db
from backend.api import (
    api_router,
    image_scan_router,
    media_scan_router,
    media_compliance_router,
    rulebook_router,
    rules_router,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite/SQLAlchemy schema on startup
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Intelligent Pre-Flight Brand Governance & Multi-Modal Compliance Engine.",
    lifespan=lifespan,
)

# CORS Middleware (supports local dev servers, VS Code Live Server, and configured origins)
allowed_origins = list(set(
    settings.BACKEND_CORS_ORIGINS + [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler for real traceback visibility during dev
@app.exception_handler(Exception)
async def show_errors(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})


# 1. Core API v1 routes (/api/v1/brands, /api/v1/verify, /api/v1/rules, /api/v1/scans)
app.include_router(api_router, prefix=settings.API_V1_STR)

# 2. Direct Media, Image, Audio & Video Scanner routes
app.include_router(image_scan_router)
app.include_router(media_scan_router)
app.include_router(media_compliance_router)
app.include_router(rulebook_router)
app.include_router(rules_router)


# 3. Health check
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": "1.0.0"}


# 4. Static and Frontend HTML pages
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
