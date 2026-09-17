"""Runtime configuration.

Every AI capability is behind a flag that defaults to *off when unconfigured*.
The deterministic planner is the product; the AI layers are enhancements that
must degrade cleanly. A missing API key is a normal operating condition here,
not an error.
"""

import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict


def _flag(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off", ""}


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    port: int = 8000
    cors_origins: list[str] = []
    catalog_path: str | None = None

    gemini_api_key: str | None = None
    vision_enabled: bool = True
    vision_model: str = "gemini-2.0-flash"
    llm_enabled: bool = True
    llm_model: str = "gemini-2.0-flash"

    @property
    def vision_available(self) -> bool:
        """Vision needs both the flag and a key. Either missing means fallback."""
        return self.vision_enabled and bool(self.gemini_api_key)

    @property
    def llm_available(self) -> bool:
        return self.llm_enabled and bool(self.gemini_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return Settings(
        port=int(os.getenv("PORT", "8000")),
        cors_origins=[origin.strip() for origin in origins.split(",") if origin.strip()],
        catalog_path=os.getenv("CATALOG_PATH"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        vision_enabled=_flag("VISION_ENABLED"),
        vision_model=os.getenv("GEMINI_VISION_MODEL", "gemini-2.0-flash"),
        llm_enabled=_flag("LLM_ENABLED"),
        llm_model=os.getenv("GEMINI_LLM_MODEL", "gemini-2.0-flash"),
    )
