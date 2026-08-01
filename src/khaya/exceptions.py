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


class AuthenticationError(APIError):
    """Error during authentication."""


class RateLimitError(APIError):
    """Error during rate limiting."""


class TranslationError(APIError):
    """Error during translation."""


class TTSGenerationError(APIError):
    """Error during TTS generation."""


class ASRTranscriptionError(APIError):
    """Error during ASR transcription."""
