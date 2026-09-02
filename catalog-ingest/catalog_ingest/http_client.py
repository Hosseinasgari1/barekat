"""Rate-limited async HTTP client with UA rotation and retries."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

from curl_cffi import requests as cffi_requests
import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from catalog_ingest.config import Settings, get_settings

logger = logging.getLogger(__name__)

USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
)


class RateLimitError(Exception):
    def __init__(self, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(f"Rate limited (Retry-After={retry_after})")


class ServerError(Exception):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Server error HTTP {status_code}")


def _should_retry(exc: BaseException) -> bool:
    return isinstance(exc, (RateLimitError, ServerError, httpx.TimeoutException, httpx.TransportError, Exception))


class TokenBucket:
    """Simple async token-bucket rate limiter."""

    def __init__(self, rate: float) -> None:
        self.rate = max(rate, 0.05)
        self.tokens = self.rate
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.updated_at
                self.updated_at = now
                self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait)


class RateLimitedClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._bucket = TokenBucket(self.settings.rate_limit_rps)
        self._client: cffi_requests.AsyncSession | None = None

    async def __aenter__(self) -> RateLimitedClient:
        self._client = cffi_requests.AsyncSession(
            impersonate="chrome",
            timeout=self.settings.http_timeout_seconds,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
                "Referer": "https://snapp.market/"
            },
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {}
        if self.settings.snapp_cookie:
            headers["Cookie"] = self.settings.snapp_cookie
        if extra:
            headers.update(extra)
        return headers

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        await self._bucket.acquire()
        return await self._get_json_with_retry(url, params=params, headers=headers)

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> str:
        await self._bucket.acquire()
        return await self._get_text_with_retry(url, params=params, headers=headers)

    def _retry_decorator(self):
        return retry(
            reraise=True,
            stop=stop_after_attempt(self.settings.http_max_retries),
            wait=wait_exponential_jitter(initial=1, max=30),
            retry=retry_if_exception(_should_retry),
            before_sleep=lambda rs: logger.warning(
                "Retry %s after %s: %s",
                rs.attempt_number,
                rs.next_action,
                rs.outcome.exception() if rs.outcome else None,
            ),
        )

    async def _get_json_with_retry(
        self,
        url: str,
        *,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> Any:
        @self._retry_decorator()
        async def _do() -> Any:
            assert self._client is not None
            response = await self._client.get(
                url, params=params, headers=self._headers(headers)
            )
            self._raise_for_status(response)
            return response.json()

        return await _do()

    async def _get_text_with_retry(
        self,
        url: str,
        *,
        params: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> str:
        @self._retry_decorator()
        async def _do() -> str:
            assert self._client is not None
            response = await self._client.get(
                url, params=params, headers=self._headers(headers)
            )
            self._raise_for_status(response)
            return response.text

        return await _do()

    @staticmethod
    def _raise_for_status(response: Any) -> None:
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else None
            raise RateLimitError(delay)
        if response.status_code >= 500 or response.status_code == 403:
            raise ServerError(response.status_code)
        response.raise_for_status()
