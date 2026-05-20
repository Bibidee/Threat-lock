"""Centralized configuration for the Threat-Lock backend.

All settings come from environment variables, loaded from the repo-root `.env`
(copied from `.env.example`). We use pydantic-settings so values are typed and
validated at startup, and missing-but-required values fail loudly.

Nothing secret is hard-coded here — only safe defaults.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = .../Threat-lock  (this file is backend/app/core/config.py)
REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- GenLayer ----
    genlayer_rpc_url: str = "https://studio.genlayer.com/api"
    genlayer_chain_id: int = 61999
    genlayer_network: str = "studionet"
    genlayer_private_key: str = ""  # operator key; empty => read-only mode
    threatlock_contract_address: str = ""  # filled after deploy

    # ---- Firebase ----
    firebase_service_account: str = "firebase/serviceAccountKey.json"
    firebase_project_id: str = ""

    # ---- API ----
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # ---- Monitoring ----
    threat_pause_threshold: int = 75
    monitor_interval_seconds: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v):
        """Accept a comma-separated string from .env or an already-parsed list."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ---- Convenience flags ----
    @property
    def genlayer_write_enabled(self) -> bool:
        """True when we have both an operator key and a deployed contract."""
        return bool(self.genlayer_private_key) and bool(self.threatlock_contract_address)

    @property
    def firebase_key_path(self) -> Path:
        p = Path(self.firebase_service_account)
        return p if p.is_absolute() else (REPO_ROOT / p)

    @property
    def firebase_enabled(self) -> bool:
        return self.firebase_key_path.exists()


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so the .env is read once per process."""
    return Settings()
