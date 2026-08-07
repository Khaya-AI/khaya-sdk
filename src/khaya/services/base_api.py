import asyncio
import logging
import random
import re
import time
from typing import Any

import httpx

from khaya.config import Settings
from khaya.exceptions import APIError, AuthenticationError, RateLimitError

logger = logging.getLogger(__name__)

# Status codes that warrant a retry.
_RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})

# Upper bound on a server-supplied Retry-After delay. Without a cap, a
# misconfigured or hostile server can block the caller indefinitely.
MAX_RETRY_AFTER_SECONDS = 60.0

# Error bodies are not always JSON — gateways return HTML pages. Keep the
# fallback message short rather than embedding a whole document.
_MAX_SNIPPET_CHARS = 200


def _non_json_message(response: httpx.Response) -> str:
    """Build a readable message from a non-JSON error body.

    Gateways return full HTML pages when a backend is unavailable; the useful
    signal is the page title, not several kilobytes of inline CSS.
    """
    prefix = f"HTTP {response.status_code}"
    text = response.text
    title = re.search(r"<title[^>]*>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    if title:
        summary = " ".join(title.group(1).split())
        if summary:
            return f"{prefix}: {summary} (non-JSON response from the API gateway)"
    snippet = " ".join(text.split())[:_MAX_SNIPPET_CHARS]
    return f"{prefix}: {snippet}" if snippet else prefix


def _parse_error_body(response: httpx.Response) -> dict[str, Any]:
    """Extract structured fields from an API error body.

    Handles the two envelopes the Khaya API uses::

        {"statusCode": 500, "message": "...", "activityId": "..."}
        {"error": {"code": "...", "message": "...", "details": [...]}}

    Falls back to a truncated body snippet for non-JSON responses (e.g. the
    HTML pages emitted by the API gateway when a backend is unavailable).
    """
    try:
        body = response.json()
    except ValueError:
        return {"message": _non_json_message(response)}

    if not isinstance(body, dict):
        return {"message": str(body)}

    parsed: dict[str, Any] = {"activity_id": body.get("activityId")}

    error = body.get("error")
    if isinstance(error, dict):
        parsed["message"] = error.get("message") or f"HTTP {response.status_code}"
        parsed["code"] = error.get("code")
        details = error.get("details")
        parsed["details"] = details if isinstance(details, list) else None
        parsed["activity_id"] = parsed["activity_id"] or error.get("activityId")
    else:
        parsed["message"] = body.get("message") or f"HTTP {response.status_code}"
        parsed["code"] = body.get("code")

    return parsed


def _build_http_exception(response: httpx.Response) -> APIError:
    """Map an HTTP error response to the appropriate APIError subclass."""
    status = response.status_code
    fields = _parse_error_body(response)
    message = fields.pop("message")

    if status == 401:
        return AuthenticationError(message, status, **fields)

    if status == 429:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            message = f"{message} (Retry-After: {retry_after}s)"
        return RateLimitError(message, status, **fields)

    return APIError(message, status, **fields)


def decode_json(response: httpx.Response) -> Any:
    """Decode a successful response body as JSON.

    Raises:
        APIError: If the body is not valid JSON. Without this, a 2xx carrying
            an HTML or truncated body would surface a raw ``JSONDecodeError``,
            which callers cannot catch via the SDK exception hierarchy.
    """
    try:
        return response.json()
    except ValueError as e:
        content_type = response.headers.get("content-type", "unknown")
        snippet = " ".join(response.text.split())[:_MAX_SNIPPET_CHARS]
        raise APIError(
            f"Expected a JSON response but received {content_type!r}: {snippet}",
            response.status_code,
        ) from e


def _backoff_delay(attempt: int) -> float:
    """Exponential backoff with jitter, capped like Retry-After.

    Uncapped, ``retry_attempts=10`` sleeps for ~8.5 uninterruptible minutes.
    """
    return min((2**attempt) + random.uniform(0, 1), MAX_RETRY_AFTER_SECONDS)


def _retry_after_delay(response: httpx.Response | None) -> float | None:
    """Return the capped Retry-After delay, or None if absent/unparseable."""
    if response is None:
        return None
    retry_after = response.headers.get("Retry-After")
    if not retry_after:
        return None
    try:
        delay = float(retry_after)
    except (ValueError, TypeError):
        # Retry-After may also be an HTTP-date; fall back to exponential backoff.
        return None
    if delay > MAX_RETRY_AFTER_SECONDS:
        logger.debug(
            "Retry-After of %.0fs exceeds cap; using %.0fs",
            delay,
            MAX_RETRY_AFTER_SECONDS,
        )
        return MAX_RETRY_AFTER_SECONDS
    return max(delay, 0.0)


class BaseApi:
    def __init__(self, config: Settings) -> None:
        self.config = config
        # Clients are created on first use so that a purely synchronous caller
        # never allocates an AsyncClient (and vice versa) — an unused client
        # would otherwise be left open when the context manager exits.
        self._sync_client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

    @property
    def sync_client(self) -> httpx.Client:
        if self._sync_client is None:
            self._sync_client = httpx.Client(timeout=self.config.timeout)
        return self._sync_client

    @property
    def async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._async_client

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
        """Close the synchronous client, if one was created."""
        if self._sync_client is not None:
            self._sync_client.close()

    async def aclose(self) -> None:
        """Close both clients, if they were created."""
        if self._async_client is not None:
            await self._async_client.aclose()
        self.close()

    def _prepare_headers(self) -> dict[str, str]:
        return {
            "Ocp-Apim-Subscription-Key": self.config.api_key or "",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }

    def _sync_backoff(self, attempt: int, response: httpx.Response | None = None) -> None:
        delay = _retry_after_delay(response)
        if delay is not None:
            logger.debug("Respecting Retry-After header: sleeping %.1fs", delay)
            time.sleep(delay)
            return
        delay = _backoff_delay(attempt)
        logger.debug("Backing off %.1fs before next attempt", delay)
        time.sleep(delay)

    async def _async_backoff(self, attempt: int, response: httpx.Response | None = None) -> None:
        delay = _retry_after_delay(response)
        if delay is not None:
            logger.debug("Respecting Retry-After header: sleeping %.1fs", delay)
            await asyncio.sleep(delay)
            return
        delay = _backoff_delay(attempt)
        logger.debug("Backing off %.1fs before next attempt", delay)
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
        total = self.config.retry_attempts

        for attempt in range(total):
            try:
                logger.debug("HTTP %s %s (attempt %d/%d)", method, url, attempt + 1, total)
                response = self.sync_client.request(method, url, **kwargs)

                if response.status_code in _RETRYABLE_STATUS_CODES and attempt < total - 1:
                    last_exc = _build_http_exception(response)
                    logger.warning(
                        "Received %d from %s %s — retrying (attempt %d/%d)",
                        response.status_code,
                        method,
                        url,
                        attempt + 1,
                        total,
                    )
                    self._sync_backoff(attempt, response)
                    continue

                if response.is_error:
                    raise _build_http_exception(response)

                logger.debug("Response %d: %s %s", response.status_code, method, url)
                return response

            except APIError:
                raise
            except httpx.TransportError as e:
                if attempt < total - 1:
                    logger.warning(
                        "Transport error on %s %s: %s — retrying (attempt %d/%d)",
                        method,
                        url,
                        e,
                        attempt + 1,
                        total,
                    )
                    self._sync_backoff(attempt)
                    continue
                logger.warning("Transport error on final attempt: %s %s — %s", method, url, e)
                raise APIError(f"Transport error: {e}", 0) from e

        if last_exc is not None:  # pragma: no cover
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
        total = self.config.retry_attempts

        for attempt in range(total):
            try:
                logger.debug("HTTP %s %s (attempt %d/%d)", method, url, attempt + 1, total)
                response = await self.async_client.request(method, url, **kwargs)

                if response.status_code in _RETRYABLE_STATUS_CODES and attempt < total - 1:
                    last_exc = _build_http_exception(response)
                    logger.warning(
                        "Received %d from %s %s — retrying (attempt %d/%d)",
                        response.status_code,
                        method,
                        url,
                        attempt + 1,
                        total,
                    )
                    await self._async_backoff(attempt, response)
                    continue

                if response.is_error:
                    raise _build_http_exception(response)

                logger.debug("Response %d: %s %s", response.status_code, method, url)
                return response

            except APIError:
                raise
            except httpx.TransportError as e:
                if attempt < total - 1:
                    logger.warning(
                        "Transport error on %s %s: %s — retrying (attempt %d/%d)",
                        method,
                        url,
                        e,
                        attempt + 1,
                        total,
                    )
                    await self._async_backoff(attempt)
                    continue
                logger.warning("Transport error on final attempt: %s %s — %s", method, url, e)
                raise APIError(f"Transport error: {e}", 0) from e

        if last_exc is not None:  # pragma: no cover
            raise last_exc
        raise APIError("Request failed after retries", 0)  # pragma: no cover
