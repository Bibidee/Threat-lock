"""ID generation helpers."""
from __future__ import annotations

import uuid


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def threat_id() -> str:
    return new_id("threat")


def pause_event_id() -> str:
    return new_id("pause")


def audit_id() -> str:
    return new_id("audit")


def run_id() -> str:
    return new_id("run")
