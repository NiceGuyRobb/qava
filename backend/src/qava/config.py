from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

AssistanceMode = Literal["disabled", "fixture"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="QAVA_")

    database_url: str = "sqlite+aiosqlite:///.local/qava.db"
    artifact_root: Path = Path(".local/artifacts")
    trusted_identity_header: str = "X-Qava-Identity"
    assistance_mode: AssistanceMode = "disabled"

    # Foundation limits from plan constraints.
    max_collection_depth: int = Field(default=3, ge=1)
    max_collection_items: int = Field(default=100, ge=1)
    max_clarification_followups: int = Field(default=2, ge=0)
    max_interactions_per_session: int = Field(default=1000, ge=1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
