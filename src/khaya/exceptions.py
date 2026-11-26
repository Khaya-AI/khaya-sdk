from typing import Any


class APIError(Exception):
    """Base class for API errors.

    Attributes:
        message: Human-readable error message. When the API returns a
            structured error envelope, this is the message it carried.
        status_code: HTTP status code, or 0 for transport-level failures.
        code: Machine-readable error code from the API (e.g.
            ``"VALIDATION_FAILED"``), when one was supplied.
        details: Per-field error details from the API, when supplied.
        activity_id: Server-side correlation ID. Quote this when reporting
            a problem to Khaya support.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        *,
        code: str | None = None,
        details: list[dict[str, Any]] | None = None,
        activity_id: str | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or []
        self.activity_id = activity_id
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.code:
            parts.append(f"code={self.code}")
        if self.activity_id:
            parts.append(f"activityId={self.activity_id}")
        for detail in self.details:
            target, msg = detail.get("target"), detail.get("message")
            if target and msg:
                parts.append(f"{target}: {msg}")
            elif msg:
                parts.append(str(msg))
        return " | ".join(parts)


class APIConnectionError(APIError):
    """The request never got an HTTP response (``status_code`` is 0).

    Raised for a refused connection or DNS failure once the retries run out.
    """


class APITimeoutError(APIConnectionError):
    """The request timed out.

    A timeout after the request was sent is not retried: the API may still
    have processed and billed it. Raise ``timeout`` for long audio or text.
    """


class AuthenticationError(APIError):
    """The API key is missing, invalid or revoked (HTTP 401)."""


class BadRequestError(APIError):
    """The API rejected the request's parameters (HTTP 400 or 422).

    ``details`` names each offending field. Not retried: fix the call.
    """


class PermissionDeniedError(APIError):
    """The key is valid but may not do this (HTTP 403).

    ``code`` says why, for example ``ROUTE_NOT_ALLOWED`` or ``SIGNUP_REQUIRED``.
    """


class NotFoundError(APIError):
    """The route does not exist (HTTP 404). Check ``base_url``."""


class RateLimitError(APIError):
    """Too many requests (HTTP 429), raised once the retries run out.

    Attributes:
        retry_after: Seconds the API asked the caller to wait (its
            ``Retry-After`` header), or None if it sent none.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        *,
        retry_after: float | None = None,
        **fields: Any,
    ):
        super().__init__(message, status_code, **fields)
        self.retry_after = retry_after


class InsufficientCreditsError(APIError):
    """The account's credit balance cannot cover the request (HTTP 402).

    Not retried: the request will keep failing until the balance is topped up.
    """


class PayloadTooLargeError(APIError):
    """The request body exceeds the gateway's size limit (HTTP 413).

    The platform error code is ``REQUEST_TOO_LARGE``. Not retried: send less
    data, for example a shorter audio clip or less text.
    """


class UnsupportedMediaTypeError(APIError):
    """The request's Content-Type is not accepted by the route (HTTP 415).

    The platform error code is ``UNSUPPORTED_MEDIA_TYPE``. Not retried. ASR
    takes ``audio/*``, ``video/*`` or ``application/octet-stream``; translation
    and TTS take ``application/json``. The SDK sets the right type itself, so
    this points at a custom header or a proxy rewriting the request.
    """


class ServerError(APIError):
    """The platform failed to handle the request (HTTP 5xx).

    A 500, 502, 503 or 504 is retried with backoff and this is raised once the
    attempts run out; any other 5xx is raised straight away. Quote
    ``activity_id`` when reporting it to Khaya support.
    """


class TranslationError(APIError):
    """Bad input to ``translate()``, caught before any request is sent."""


class TTSGenerationError(APIError):
    """Bad input to ``synthesize()``, or a response that is not audio."""


class ASRTranscriptionError(APIError):
    """Bad input to ``transcribe()``, caught before any request is sent."""
