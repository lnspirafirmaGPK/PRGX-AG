from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class GemOfWisdom(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    lesson: str
    param_update: dict[str, Any]
    scope: str
    safe_to_apply: bool = True
