from fastapi import APIRouter

from backend.api.image_scan import router as image_scan_router
from backend.api.media_scan import router as media_scan_router
from backend.api.text_scan import router as text_scan_router

router = APIRouter()
router.include_router(image_scan_router)
router.include_router(media_scan_router)
router.include_router(text_scan_router)