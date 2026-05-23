"""Central configuration for the Threat-Lock backend.

All settings come from environment variables (root `.env`). Real integrations are
the primary path; local fallbacks only kick in when credentials are missing.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# backend/app/config.py -> parents[2] == repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"

CsvList = Annotated[list[str], NoDecode]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- app ----
    app_env: str = "local"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    backend_api_key: str = ""

    # ---- Firebase ----
    firebase_project_id: str = ""
    firebase_client_email: str = ""
    firebase_private_key: str = ""
    # path-based service account (alternative to the 3 fields above)
    firebase_service_account: str = "firebase/serviceAccountKey.json"

    # ---- GenLayer ----
    genlayer_mode: str = "real"  # "real" | "local"
    genlayer_contract_address: str = ""
    genlayer_rpc_url: str = "https://studio.genlayer.com/api"
    genlayer_private_key: str = ""
    genlayer_chain_id: int = 61999
    genlayer_studionet: bool = True
    admin_wallet_address: str = ""

    # ---- Protected demo protocol (Aegis Vault) ----
    aegis_vault_address: str = ""

    # ---- Explorer monitoring ----
    explorer_provider: str = ""
    explorer_api_key: str = ""
    explorer_base_url: str = ""
    watched_chain: str = ""
    watched_protocol_address: str = ""
    watched_treasury_address: str = ""
    monitored_protocol_name: str = ""
    monitored_protocol_keywords: CsvList = Field(default_factory=list)
    monitored_wallets: CsvList = Field(default_factory=list)
    suspicious_wallets: CsvList = Field(default_factory=list)

    # ---- News / security feeds ----
    news_rss_urls: CsvList = Field(
        default_factory=lambda: [
            "https://cointelegraph.com/rss/tag/security",
            "https://www.theblock.co/rss.xml",
        ]
    )
    security_keywords: CsvList = Field(
        default_factory=lambda: [
            "hack", "exploit", "drain", "bridge exploit", "oracle manipulation",
            "reentrancy", "private key compromised", "treasury drained",
            "protocol attack", "rug", "governance attack", "flash loan attack",
        ]
    )

    @field_validator(
        "monitored_protocol_keywords", "monitored_wallets", "suspicious_wallets",
        "news_rss_urls", "security_keywords", mode="before",
    )
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("suspicious_wallets", "monitored_wallets", mode="after")
    @classmethod
    def _lower(cls, v: list[str]) -> list[str]:
        return [a.lower() for a in v]

    # ---- derived flags ----
    @property
    def genlayer_real(self) -> bool:
        return (
            self.genlayer_mode.lower() == "real"
            and bool(self.genlayer_contract_address)
            and bool(self.genlayer_private_key)
        )

    @property
    def vault_enabled(self) -> bool:
        return self.genlayer_mode.lower() == "real" and bool(self.aegis_vault_address)

    @property
    def firebase_key_path(self) -> Path:
        p = Path(self.firebase_service_account)
        return p if p.is_absolute() else (REPO_ROOT / p)

    @property
    def firebase_enabled(self) -> bool:
        if self.firebase_project_id and self.firebase_client_email and self.firebase_private_key:
            return True
        return self.firebase_key_path.exists()

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origin.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
