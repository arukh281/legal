"""Raw HTTP client transport.

Normative source:
- Session S04 Directive #1: The raw transport lives in core/http_client.py,
  and only core/http_client.py may import httpx, requests, urllib.request or aiohttp.
  The raw transport must be private and only obtainable through GatedHttpClient.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

import httpx
import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RawHttpResponse:
    """Immutable representation of an HTTP response."""

    status_code: int
    headers: dict[str, str]
    content: bytes
    url: str

    @property
    def text(self) -> str:
        return self.content.decode("utf-8", errors="replace")


class RawHttpClient:
    """Private low-level HTTP transport.

    CANNOT be used directly by application code or adapters.
    Can ONLY be instantiated by GatedHttpClient in ingest.gate.
    """

    def __init__(self, *, default_timeout: float = 30.0) -> None:
        caller_module = sys._getframe(1).f_globals.get("__name__", "")
        # Allow instantiation from ingest.gate and during tests
        if not (
            caller_module.startswith("ingest.gate")
            or caller_module.startswith("core.http_client")
            or "test" in caller_module
        ):
            raise PermissionError(
                f"Unauthorized instantiation of RawHttpClient from module '{caller_module}'. "
                "Network calls must go exclusively through GatedHttpClient."
            )
        self.default_timeout = default_timeout
        # TLS verification is strictly enabled - never disabled (02_P0 §5.8)
        self._client = httpx.Client(
            verify=True,
            timeout=default_timeout,
            follow_redirects=True,
        )

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> RawHttpResponse:
        resp = self._client.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout or self.default_timeout,
        )
        return RawHttpResponse(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            content=resp.content,
            url=str(resp.url),
        )

    def post(
        self,
        url: str,
        *,
        data: dict[str, Any] | None = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> RawHttpResponse:
        resp = self._client.post(
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=timeout or self.default_timeout,
        )
        return RawHttpResponse(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            content=resp.content,
            url=str(resp.url),
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> RawHttpClient:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def fetch_policy_snapshot(url: str, *, timeout: float = 30.0) -> tuple[int, bytes, str]:
    """Fetch an official policy or robots snapshot for legal profile onboarding (Directive #5).

    Used exclusively for initial legal profile bootstrapping and terms archiving.
    """
    caller_module = sys._getframe(1).f_globals.get("__name__", "")
    if not (
        caller_module.startswith("ingest.management.commands.seed_ibbi_profile")
        or caller_module.startswith("core.http_client")
        or "test" in caller_module
    ):
        raise PermissionError(f"Unauthorized call to fetch_policy_snapshot from '{caller_module}'.")

    ua = getattr(settings, "CRAWLER_USER_AGENT", "LegalIntelligenceBot/1.0")
    with httpx.Client(verify=True, timeout=timeout, follow_redirects=True) as client:
        resp = client.get(url, headers={"User-Agent": ua})
        content_type = resp.headers.get("content-type", "text/html")
        return resp.status_code, resp.content, content_type
