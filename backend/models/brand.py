"""
Brand and Rulebook Data Models
Defines brand profiles, active compliance rulebooks, and visual asset schemas.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BrandAsset(BaseModel):
    id: str
    name: str
    asset_type: str  # logo, vector, font, audio_stem, guidelines_pdf
    url: str
    file_size_kb: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Rulebook(BaseModel):
    id: str
    name: str
    version: str
    industry: str
    rules_count: int = 0
    summary: str
    content: Optional[str] = None
    is_active: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BrandProfile(BaseModel):
    id: str
    name: str
    initials: str
    industry: str
    color_palette: List[str] = Field(default_factory=lambda: ["#ffffff", "#a1a1aa", "#121214"])
    active_rulebook: Rulebook
    assets: List[BrandAsset] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BrandCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    industry: str = Field(..., min_length=2, max_length=80)
    rulebook_name: Optional[str] = "Standard Compliance v1.0"
    guidelines_text: Optional[str] = None
