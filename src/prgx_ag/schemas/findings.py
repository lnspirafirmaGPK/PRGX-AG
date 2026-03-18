from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from prgx_ag.schemas.enums import EthicalStatus


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    category: str
    message: str
    path: str | None = None
    severity: EthicalStatus | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("category", "message")
    @classmethod
    def _normalize_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("path")
    @classmethod
    def _normalize_optional_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().replace("\\", "/")
        return value or None


class IssueReport(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    summary: str = "repository scan completed"
    target: str = "repository"
    dependency_issues: list[str] = Field(default_factory=list)
    structural_issues: list[str] = Field(default_factory=list)
    integrity_issues: list[str] = Field(default_factory=list)
    issue_count: int = 0
    requires_fix: bool = False
    findings: list[Finding] = Field(default_factory=list)

    @field_validator("summary", "target")
    @classmethod
    def _normalize_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("issue_count")
    @classmethod
    def _non_negative_issue_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("issue_count must be >= 0")
        return value
