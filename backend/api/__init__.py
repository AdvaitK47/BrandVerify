"""BrandVerify REST API Router"""
from fastapi import APIRouter
from .brands import router as brands_router
from .verify import router as verify_router
from .rules import router as rules_router
from .scans import router as scans_router

api_router = APIRouter()
api_router.include_router(brands_router, prefix="/brands", tags=["Brands"])
api_router.include_router(verify_router, prefix="/verify", tags=["Compliance Verification"])
api_router.include_router(rules_router, prefix="/rules", tags=["Rulebooks & Policies"])
api_router.include_router(scans_router, prefix="/scans", tags=["Scan History"])
