"""
BrandVerify Application Configuration
Pydantic Settings for Environment Variables, Security, and ML Service Endpoints.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "BrandVerify Engine"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "brandverify_super_secret_development_key_928374")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./brandverify.db")
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000"
    ]
    
    # AI / Model Providers
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY", None)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GROQ_API_KEY: Optional[str] = None

    # Verification Engine Settings
    DELTA_E_THRESHOLD: float = 2.5  # CIE2000 acceptable brand color tolerance
    MIN_LOGO_MARGIN_PX: int = 32     # Minimum required exclusion margin
    MAX_SPEECH_WPM: int = 160        # Max comfortable spoken words per minute

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
