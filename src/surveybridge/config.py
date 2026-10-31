"""Local configuration; remote destinations cannot be supplied by tool callers."""

import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    base_url: str = "https://api.dhsprogram.com/rest/dhs"
    workspace: Path = Field(
        default_factory=lambda: Path(os.getenv("SURVEYBRIDGE_WORKSPACE", ".surveybridge")).resolve()
    )
    output_root: Path = Field(
        default_factory=lambda: Path(os.getenv("SURVEYBRIDGE_OUTPUT_ROOT", "outputs")).resolve()
    )
    timeout: float = Field(default=30, gt=0, le=120)
    retries: int = Field(default=3, ge=0, le=5)
    max_pages: int = Field(default=100, ge=1, le=1000)
    per_page: int = Field(default=1000, ge=1, le=1000)
    cache_seconds: int = Field(default=86400, ge=0)
    offline: bool = Field(default_factory=lambda: os.getenv("SURVEYBRIDGE_OFFLINE", "0") == "1")

    @field_validator("base_url")
    @classmethod
    def official_origin(cls, value: str) -> str:
        if value.rstrip("/") != "https://api.dhsprogram.com/rest/dhs":
            raise ValueError("Only the official HTTPS DHS aggregate API is allowed")
        return value.rstrip("/")
