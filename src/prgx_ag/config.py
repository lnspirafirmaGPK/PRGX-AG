from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

RuntimeProfileName = Literal['development', 'staging', 'production']


class RuntimeProfile(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    name: RuntimeProfileName
    max_auto_fix_items: int
    max_issue_count_for_auto_fix: int
    audit_verbosity: Literal['compact', 'standard', 'forensic']
    evidence_signature_required: bool


RUNTIME_PROFILES: dict[RuntimeProfileName, RuntimeProfile] = {
    'development': RuntimeProfile(
        name='development',
        max_auto_fix_items=20,
        max_issue_count_for_auto_fix=60,
        audit_verbosity='compact',
        evidence_signature_required=False,
    ),
    'staging': RuntimeProfile(
        name='staging',
        max_auto_fix_items=12,
        max_issue_count_for_auto_fix=30,
        audit_verbosity='standard',
        evidence_signature_required=True,
    ),
    'production': RuntimeProfile(
        name='production',
        max_auto_fix_items=5,
        max_issue_count_for_auto_fix=12,
        audit_verbosity='forensic',
        evidence_signature_required=True,
    ),
}


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables only."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    mode: str = Field(default='local', alias='PRGX_AG_MODE')
    runtime_profile: RuntimeProfileName = Field(default='development', alias='PRGX_RUNTIME_PROFILE')
    log_level: str = Field(default='INFO', alias='PRGX_AG_LOG_LEVEL')
    repo_root: Path = Field(default=Path('.'), alias='PRGX_AG_REPO_ROOT')
    dry_run: bool = Field(default=True, alias='PRGX_AG_DRY_RUN')
    github_token: str | None = Field(default=None, alias='GITHUB_TOKEN')
    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    allowed_write_paths: str | None = Field(default=None, alias='PRGX_AG_ALLOWED_WRITE_PATHS')
    protected_paths: str | None = Field(default=None, alias='PRGX_AG_PROTECTED_PATHS')
    audit_window_hours: int = Field(default=24, alias='PRGX_AUDIT_WINDOW_HOURS', ge=1)
    medical_findings_path: str = Field(
        default='.prgx-ag/evidence/medical_research_findings.json',
        alias='PRGX_MEDICAL_FINDINGS_PATH',
    )
    event_history_size: int = 150

    @property
    def profile(self) -> RuntimeProfile:
        return RUNTIME_PROFILES[self.runtime_profile]


class RuntimePaths(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    allowed: list[str] = Field(default_factory=lambda: ['src/', 'tests/', '.github/workflows/', '.prgx-ag/'])
    protected: list[str] = Field(default_factory=lambda: ['.git/', '.github/CODEOWNERS', '.env', '.env.*', '*.pem', '*.key'])


def parse_path_list(raw: str | None, fallback: list[str]) -> list[str]:
    if not raw:
        return fallback
    return [item.strip() for item in raw.split(',') if item.strip()]
