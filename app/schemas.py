from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.probes import ProbeError, validate_url


class TargetCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    url: str = Field(min_length=8, max_length=500)
    interval_minutes: int = Field(default=30, ge=5, le=10_080)
    render_js: bool = False

    @field_validator("url")
    @classmethod
    def check_url(cls, value: str) -> str:
        try:
            return validate_url(value.strip())
        except ProbeError as error:
            raise ValueError(str(error)) from error
