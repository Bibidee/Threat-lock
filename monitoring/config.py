"""Configuration for the monitoring workers (reads the repo-root .env)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / ".env"


class MonitorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- backend ----
    backend_url: str = "http://localhost:8000"
    monitor_api_token: str = ""

    # ---- loop ----
    monitor_interval_seconds: int = 30
    monitor_simulate: bool = True
    monitor_report_floor: int = 40
    monitor_cooldown_seconds: int = 120
    threat_pause_threshold: int = 75

    # ---- volume-spike detector ----
    volume_window: int = 20
    volume_z_threshold: float = 3.0
    metrics_url: str = ""

    # ---- news / feeds ----
    # NoDecode: keep pydantic-settings from JSON-parsing these env vars so our
    # comma-separated-string validator below handles them.
    news_feed_urls: Annotated[list[str], NoDecode] = Field(default_factory=list)
    watchlist_terms: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "exploit", "hack", "drain", "reentrancy", "rug pull",
            "private key", "backdoor", "vulnerability", "stolen",
        ]
    )
    wallet_blacklist: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("news_feed_urls", "watchlist_terms", "wallet_blacklist", mode="before")
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("wallet_blacklist", mode="after")
    @classmethod
    def _lower_addrs(cls, v: list[str]) -> list[str]:
        return [a.lower() for a in v]


@lru_cache
def get_monitor_settings() -> MonitorSettings:
    return MonitorSettings()
