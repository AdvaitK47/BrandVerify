"""
BrandVerify REST API Router Aggregation
Combines core governance, multi-modal verification, and media compliance engines.
"""

from fastapi import APIRouter

# Core governance & audit routers
from .brands import router as brands_router
from .verify import router as verify_router
from .rules import router as rules_router
from .scans import router as scans_router

# Multi-modal media & compliance scanners
from .image_scan import router as image_scan_router
from .media_scan import router as media_scan_router
from .text_scan import router as text_scan_router
from .media_compliance import router as media_compliance_router
from .rulebook_compliance import router as rulebook_router

api_router = APIRouter()

# Main API v1 routes
api_router.include_router(brands_router, prefix="/brands", tags=["Brands"])
api_router.include_router(verify_router, prefix="/verify", tags=["Compliance Verification"])
api_router.include_router(rules_router, prefix="/rules", tags=["Rulebooks & Policies"])
api_router.include_router(scans_router, prefix="/scans", tags=["Scan History"])

# Dual-branch alias
router = api_router

__all__ = [
    "api_router",
    "router",
    "brands_router",
    "verify_router",
    "rules_router",
    "scans_router",
    "image_scan_router",
    "media_scan_router",
    "text_scan_router",
    "media_compliance_router",
    "rulebook_router",
]
