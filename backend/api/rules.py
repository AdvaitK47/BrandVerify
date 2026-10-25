"""
Rulebooks and Regulatory Policy Endpoints
"""

from fastapi import APIRouter
from typing import List
from backend.models.brand import Rulebook

router = APIRouter(
    prefix="/api/rules",
    tags=["Rulebooks"]
)

GLOBAL_RULEBOOKS: List[Rulebook] = [
    Rulebook(
        id="ftc-cloud-v3",
        name="FTC Tech & Cloud Claims v3.2",
        version="3.2",
        industry="Enterprise Cloud & SaaS",
        rules_count=18,
        summary="Automated substantiation for uptime claims, latency comparisons, and multi-tenant isolation claims."
    ),
    Rulebook(
        id="eu-green-v2",
        name="EU Green Claims Directive v2.8",
        version="2.8",
        industry="Sustainability & Retail",
        rules_count=24,
        summary="Requires life-cycle assessments (LCA) and third-party verification for climate neutrality claims."
    ),
    Rulebook(
        id="sec-10b5",
        name="SEC Disclosure Rule 10b-5",
        version="10b-5",
        industry="Asset Management & FinTech",
        rules_count=31,
        summary="Mandatory safe harbor footnotes, risk disclaimer legibility duration, and verified past performance disclosures."
    ),
    Rulebook(
        id="fda-claims-v4",
        name="FDA Dietary Health Claims v4.1",
        version="4.1",
        industry="Clinical Biotechnology & Nutrition",
        rules_count=42,
        summary="Double-blind clinical trial references required for efficacy statements; strict dietary supplement disclaimers."
    ),
]

@router.get("", response_model=List[Rulebook])
async def list_rulebooks():
    """Retrieve all available pre-packaged regulatory rulebooks."""
    return GLOBAL_RULEBOOKS
