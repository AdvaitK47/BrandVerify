"""
Brands API Endpoints
Full CRUD operations for managed brand profiles and their associated rulebooks.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict
from backend.models.brand import BrandProfile, BrandCreateRequest, Rulebook

router = APIRouter()

# In-memory database seeded with default enterprise brand profiles
MOCK_BRANDS_DB: Dict[str, BrandProfile] = {
    "acme-tech": BrandProfile(
        id="acme-tech",
        name="Acme Global Technologies",
        initials="AT",
        industry="Enterprise Cloud & SaaS",
        color_palette=["#ffffff", "#a1a1aa", "#121214"],
        active_rulebook=Rulebook(
            id="rulebook-acme",
            name="FTC Tech & Cloud Claims v3.2",
            version="3.2",
            industry="Enterprise Cloud & SaaS",
            rules_count=18,
            summary="Rigorous uptime substantiation, multi-tenant benchmark rules, and zero deceptive performance claims."
        )
    ),
    "luxe-fashion": BrandProfile(
        id="luxe-fashion",
        name="Luxe & Co. Haute Couture",
        initials="LC",
        industry="Luxury Fashion & Retail",
        color_palette=["#ffffff", "#71717a", "#000000"],
        active_rulebook=Rulebook(
            id="rulebook-luxe",
            name="EU Green Claims Directive v2.8",
            version="2.8",
            industry="Luxury Fashion & Retail",
            rules_count=24,
            summary="Strict sustainability claim substantiation, organic certification references, and gold foil exclusion margins."
        )
    ),
    "apex-fin": BrandProfile(
        id="apex-fin",
        name="Apex Financial Partners",
        initials="AF",
        industry="Asset Management & FinTech",
        color_palette=["#ffffff", "#d4d4d8", "#08080a"],
        active_rulebook=Rulebook(
            id="rulebook-apex",
            name="SEC Disclosure Rule 10b-5",
            version="10b-5",
            industry="Asset Management & FinTech",
            rules_count=31,
            summary="Mandatory safe harbor footnotes, risk disclaimer legibility duration, and verified past performance disclosures."
        )
    ),
    "pulse-health": BrandProfile(
        id="pulse-health",
        name="Pulse BioHealth & Nutrition",
        initials="PB",
        industry="Clinical Biotechnology",
        color_palette=["#ffffff", "#a1a1aa", "#18181b"],
        active_rulebook=Rulebook(
            id="rulebook-pulse",
            name="FDA Dietary Health Claims v4.1",
            version="4.1",
            industry="Clinical Biotechnology",
            rules_count=42,
            summary="Double-blind clinical trial references required for efficacy statements; strict dietary supplement disclaimers."
        )
    ),
}

@router.get("", response_model=List[BrandProfile])
async def list_brands():
    """Retrieve all managed brand profiles."""
    return list(MOCK_BRANDS_DB.values())

@router.get("/{brand_id}", response_model=BrandProfile)
async def get_brand(brand_id: str):
    """Retrieve a single brand profile by ID."""
    if brand_id not in MOCK_BRANDS_DB:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return MOCK_BRANDS_DB[brand_id]

@router.post("", response_model=BrandProfile, status_code=status.HTTP_201_CREATED)
async def create_brand(payload: BrandCreateRequest):
    """Create a new brand profile."""
    brand_id = "brand-" + payload.name.lower().replace(" ", "-")[:24]
    initials = "".join([part[0] for part in payload.name.split()[:2]]).upper()

    new_brand = BrandProfile(
        id=brand_id,
        name=payload.name,
        initials=initials,
        industry=payload.industry,
        color_palette=["#ffffff", "#a1a1aa", "#121214"],
        active_rulebook=Rulebook(
            id=f"rulebook-{brand_id}",
            name=payload.rulebook_name or "Custom Rulebook v1.0",
            version="1.0",
            industry=payload.industry,
            rules_count=12,
            summary="Custom brand governance guidelines configured."
        )
    )
    MOCK_BRANDS_DB[brand_id] = new_brand
    return new_brand

@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(brand_id: str):
    """Delete a brand profile."""
    if brand_id not in MOCK_BRANDS_DB:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    del MOCK_BRANDS_DB[brand_id]
    return None
