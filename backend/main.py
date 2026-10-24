"""
BrandVerify Main Application Entrypoint
FastAPI server providing RESTful endpoints, static frontend mounting, and compliance engine routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.config import settings
from backend.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="Intelligent Pre-Flight Brand Governance & Multi-Modal Compliance Engine."
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Endpoints
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount Frontend Static Assets & HTML Templates
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": "1.0.0"}

# Frontend Page Routes (when running FastAPI as unified server)
@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/dashboard.html", include_in_schema=False)
async def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

@app.get("/brand.html", include_in_schema=False)
async def serve_brand():
    return FileResponse(os.path.join(FRONTEND_DIR, "brand.html"))

@app.get("/submission.html", include_in_schema=False)
async def serve_submission():
    return FileResponse(os.path.join(FRONTEND_DIR, "submission.html"))

@app.get("/review.html", include_in_schema=False)
async def serve_review():
    return FileResponse(os.path.join(FRONTEND_DIR, "review.html"))

@app.get("/login.html", include_in_schema=False)
async def serve_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
