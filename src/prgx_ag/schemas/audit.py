from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from prgx_ag.schemas.enums import EthicalStatus


class AuditResult(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    is_allowed: bool
    status: EthicalStatus
    reason: str | None = None
    suggested_action: str | None = None
