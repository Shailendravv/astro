"""Runtime settings, read from environment variables (docs/deployment.md section 4).

No setting that affects security has a fallback: a missing value is an error, in line with the
project rule that nothing is chosen silently. Model IDs are *optional* and empty by default:
an empty ID keeps AI features disabled (D-012, D-030). No model ID is ever written in code.
"""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", case_sensitive=False)

    app_env: Literal["dev", "test", "local-prod"]
    database_url: str
    # Comma-separated lists, e.g. "http://127.0.0.1:3000".
    allowed_origins: str
    allowed_hosts: str
    git_commit: str = Field(default="unknown", description="Set at image build time")

    # AI configuration: optional, empty = AI features disabled (MODEL_NOT_VERIFIED).
    runtime_provider: str = ""
    runtime_model_id: str = ""

    @field_validator("allowed_origins", "allowed_hosts")
    @classmethod
    def _not_empty(cls, value: str) -> str:
        if not _split_csv(value):
            raise ValueError("must list at least one entry")
        if "*" in _split_csv(value):
            raise ValueError("wildcards are not allowed (docs/security.md section 2)")
        return value

    @property
    def origins(self) -> list[str]:
        return _split_csv(self.allowed_origins)

    @property
    def hosts(self) -> list[str]:
        return _split_csv(self.allowed_hosts)

    @property
    def ai_enabled(self) -> bool:
        return bool(self.runtime_provider and self.runtime_model_id)
