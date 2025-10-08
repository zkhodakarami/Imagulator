# api/app/settings.py
from typing import Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    FW_API_KEY: Optional[str] = None
    FW_BASE_URL: Optional[str] = None
    CACHE_DIR: str = "cache"
    FW_CONNECT_TIMEOUT: int = 30
    FW_REQUEST_TIMEOUT: int = 300
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_origins(cls, v: Any):
        if v is None:
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                import json
                return json.loads(s)
            return [p.strip() for p in s.split(",") if p.strip()]
        return v

settings = Settings()

# Debug output
print(f"\n{'='*60}")
print(f"[SETTINGS] FW_API_KEY configured: {bool(settings.FW_API_KEY)}")
if settings.FW_API_KEY:
    key_preview = f"{settings.FW_API_KEY[:25]}...{settings.FW_API_KEY[-4:]}" if len(settings.FW_API_KEY) > 30 else settings.FW_API_KEY
    print(f"[SETTINGS] FW_API_KEY: {key_preview}")
else:
    print("[SETTINGS] ⚠️  WARNING: FW_API_KEY is NOT set!")
    print("[SETTINGS] Create .env file with: FW_API_KEY=upenn.flywheel.io:your_key")
print(f"[SETTINGS] CACHE_DIR: {settings.CACHE_DIR}")
print(f"{'='*60}\n")