import asyncio
import logging
import random
import time
from abc import ABC

import httpx

from khaya.config import Settings
from khaya.exceptions import APIError, AuthenticationError, RateLimitError

logger = logging.getLogger("khaya")

# Status codes that warrant a retry.
_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


def _build_http_exception(response: httpx.Response) -> APIError:
    """Map an HTTP error response to the appropriate APIError subclass."""
    try:
        message = response.text
    except Exception:
        message = f"HTTP {response.status_code}"

    status = response.status_code

    if status == 401:
        return AuthenticationError(message, status)

    if status == 429:
        retry_after = response.headers.get("Retry-After")
        msg = f"{message} (Retry-After: {retry_after}s)" if retry_after else message
        return RateLimitError(msg, status)

    return APIError(message, status)


class BaseApi(ABC):
    def __init__(self, config: Settings) -> None:
        self.config = config
        self.sync_client = httpx.Client(timeout=self.config.timeout)
        self.async_client = httpx.AsyncClient(timeout=self.config.timeout)

    # --- Context manager (sync) ---

    def __enter__(self) -> "BaseApi":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # --- Context manager (async) ---

    async def __aenter__(self) -> "BaseApi":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    def close(self) -> None:
        self.sync_client.close()

    async def aclose(self) -> None:
        await self.async_client.aclose()

    def _prepare_headers(self) -> dict[str, str]:
        return {
            "Ocp-Apim-Subscription-Key": self.config.api_key or "",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

    def _sync_backoff(
        self, attempt: int, response: httpx.Response | None = None
    ) -> None:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    time.sleep(float(retry_after))
                    return
                except (ValueError, TypeError):
                    pass
        delay = (2**attempt) + random.uniform(0, 1)
        time.sleep(delay)

    async def _async_backoff(
        self, attempt: int, response: httpx.Response | None = None
    ) -> None:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    await asyncio.sleep(float(retry_after))
                    return
                except (ValueError, TypeError):
                    pass
        delay = (2**attempt) + random.uniform(0, 1)
        await asyncio.sleep(delay)

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make a synchronous HTTP request with retry logic.

        Args:
            method: HTTP method ('GET', 'POST', etc.).
            url: The URL to request.
            **kwargs: Additional arguments forwarded to httpx.

        Returns:
            httpx.Response on success.

        Raises:
            AuthenticationError: On 401.
            RateLimitError: On 429 after all retries exhausted.
            APIError: On other HTTP errors or transport failures.
        """
        headers = self._prepare_headers()
        kwargs.setdefault("headers", headers)
        last_exc: APIError | None = None

        for attempt in range(self.config.retry_attempts):
            try:
                logger.debug("Sync request: %s %s", method, url)
                response = self.sync_client.request(method, url, **kwargs)

                if (
                    response.status_code in _RETRYABLE_STATUS_CODES
                    and attempt < self.config.retry_attempts - 1
                ):
                    last_exc = _build_http_exception(response)
                    self._sync_backoff(attempt, response)
                    continue

                if response.is_error:
                    raise _build_http_exception(response)

                return response

            except APIError:
                raise
            except httpx.TransportError as e:
                if attempt < self.config.retry_attempts - 1:
                    self._sync_backoff(attempt)
                    continue
                raise APIError(f"Transport error: {e}", 0) from e

        if last_exc is not None:
            raise last_exc
        raise APIError("Request failed after retries", 0)  # pragma: no cover

    async def arequest(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make an asynchronous HTTP request with retry logic.

        Args:
            method: HTTP method ('GET', 'POST', etc.).
            url: The URL to request.
            **kwargs: Additional arguments forwarded to httpx.

        Returns:
            httpx.Response on success.

        Raises:
            AuthenticationError: On 401.
            RateLimitError: On 429 after all retries exhausted.
            APIError: On other HTTP errors or transport failures.
        """
        headers = self._prepare_headers()
        kwargs.setdefault("headers", headers)
        last_exc: APIError | None = None

        for attempt in range(self.config.retry_attempts):
            try:
                logger.debug("Async request: %s %s", method, url)
                response = await self.async_client.request(method, url, **kwargs)

                if (
                    response.status_code in _RETRYABLE_STATUS_CODES
                    and attempt < self.config.retry_attempts - 1
                ):
                    last_exc = _build_http_exception(response)
                    await self._async_backoff(attempt, response)
                    continue

                if response.is_error:
                    raise _build_http_exception(response)

                return response

            except APIError:
                raise
            except httpx.TransportError as e:
                if attempt < self.config.retry_attempts - 1:
                    await self._async_backoff(attempt)
                    continue
                raise APIError(f"Transport error: {e}", 0) from e

        if last_exc is not None:
            raise last_exc
        raise APIError("Request failed after retries", 0)  # pragma: no cover
