from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables only."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    mode: str = Field(default='local', alias='PRGX_AG_MODE')
    log_level: str = Field(default='INFO', alias='PRGX_AG_LOG_LEVEL')
    repo_root: Path = Field(default=Path('.'), alias='PRGX_AG_REPO_ROOT')
    dry_run: bool = Field(default=True, alias='PRGX_AG_DRY_RUN')
    github_token: str | None = Field(default=None, alias='GITHUB_TOKEN')
    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    allowed_write_paths: str | None = Field(default=None, alias='PRGX_AG_ALLOWED_WRITE_PATHS')
    protected_paths: str | None = Field(default=None, alias='PRGX_AG_PROTECTED_PATHS')
    event_history_size: int = 150


class RuntimePaths(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    allowed: list[str] = Field(default_factory=lambda: ['src/', 'tests/', '.github/workflows/', '.prgx-ag/'])
    protected: list[str] = Field(default_factory=lambda: ['.git/', '.github/CODEOWNERS', '.env', '.env.*', '*.pem', '*.key'])


def parse_path_list(raw: str | None, fallback: list[str]) -> list[str]:
    if not raw:
        return fallback
    return [item.strip() for item in raw.split(',') if item.strip()]
