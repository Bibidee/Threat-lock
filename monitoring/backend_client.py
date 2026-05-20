"""Async REST client the monitor uses to push signals to the backend."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import httpx


@dataclass
class BackendResult:
    ok: bool
    status_code: int
    data: Any = None
    detail: str = ""


class BackendClient:
    def __init__(self, base_url: str, token: str = "", timeout: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._client: Optional[httpx.AsyncClient] = None

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, headers=self._headers, timeout=self.timeout
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _post(self, path: str, json: dict) -> BackendResult:
        try:
            r = await self._http().post(path, json=json)
        except httpx.HTTPError as e:
            return BackendResult(ok=False, status_code=0, detail=str(e))
        return self._wrap(r)

    async def _get(self, path: str) -> BackendResult:
        try:
            r = await self._http().get(path)
        except httpx.HTTPError as e:
            return BackendResult(ok=False, status_code=0, detail=str(e))
        return self._wrap(r)

    @staticmethod
    def _wrap(r: httpx.Response) -> BackendResult:
        try:
            data = r.json()
        except Exception:
            data = r.text
        detail = ""
        if isinstance(data, dict):
            detail = str(data.get("detail", ""))
        return BackendResult(ok=r.is_success, status_code=r.status_code, data=data, detail=detail)

    # ---- API methods ----
    async def health(self) -> BackendResult:
        return await self._get("/health")

    async def get_status(self) -> BackendResult:
        return await self._get("/contract/status")

    async def report(self, score: int, reason: str, source: str) -> BackendResult:
        return await self._post(
            "/contract/report", {"score": int(score), "reason": reason, "source": source}
        )

    async def verify(self, evidence: str) -> BackendResult:
        return await self._post("/contract/verify", {"evidence": evidence})
