import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from khaya.exceptions import TTSGenerationError


def _number(value: str | None) -> int | float | None:
    """Parse a numeric header, or None when it is absent or not a number."""
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return None


@dataclass
class Usage:
    """Billing and rate limit details the gateway reports on a response.

    Every field is None when the gateway did not send the header, so check
    before using one. Anonymous keys receive only ``free_credits_remaining``.

    Attributes:
        estimated_credit_cost: Credits charged for the request
            (``X-Estimated-Credit-Cost``).
        rate_limit_per_minute: Requests per minute your plan allows
            (``X-RateLimit-Limit-Minute``).
        rate_limit_remaining_minute: Requests left in the current minute
            (``X-RateLimit-Remaining-Minute``).
        free_credits_remaining: Free credits left on an anonymous key
            (``X-Free-Credits-Remaining``).
        request_id: The platform's request ID (``X-Khaya-Request-Id``). Quote
            it when reporting a problem to Khaya support.
        correlation_id: The ID the gateway echoes for tracing
            (``X-Correlation-ID``).
    """

    estimated_credit_cost: int | float | None = None
    rate_limit_per_minute: int | float | None = None
    rate_limit_remaining_minute: int | float | None = None
    free_credits_remaining: int | float | None = None
    request_id: str | None = None
    correlation_id: str | None = None

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> "Usage | None":
        """Read the gateway's headers. Returns None if none are present."""
        usage = cls(
            estimated_credit_cost=_number(headers.get("X-Estimated-Credit-Cost")),
            rate_limit_per_minute=_number(headers.get("X-RateLimit-Limit-Minute")),
            rate_limit_remaining_minute=_number(headers.get("X-RateLimit-Remaining-Minute")),
            free_credits_remaining=_number(headers.get("X-Free-Credits-Remaining")),
            request_id=headers.get("X-Khaya-Request-Id"),
            correlation_id=headers.get("X-Correlation-ID"),
        )
        return usage if usage != cls() else None


@dataclass
class TranslationResult:
    """Result returned by `KhayaClient.translate()` and `KhayaClient.atranslate()`.

    Attributes:
        text: The translated string.
        source_language: Source language code (e.g. ``"en"``).
        target_language: Target language code (e.g. ``"tw"``).
        usage: Credit cost and rate limit headers from the response, or None
            if the gateway sent none.
    """

    text: str
    source_language: str
    target_language: str
    usage: Usage | None = field(default=None, compare=False)


@dataclass
class WordTiming:
    """When a single word was spoken.

    Attributes:
        word: The word as transcribed.
        start: Start offset in seconds.
        end: End offset in seconds.
    """

    word: str
    start: float
    end: float


@dataclass
class SegmentTiming:
    """When a contiguous span of speech was spoken.

    Attributes:
        text: The segment as transcribed.
        start: Start offset in seconds.
        end: End offset in seconds.
    """

    text: str
    start: float
    end: float


@dataclass
class Timings:
    """Alignment data, present only when ``timestamps`` was requested.

    Exactly one of ``words`` or ``segments`` is populated, matching the
    requested granularity.

    Attributes:
        unit: Unit of the offsets, currently always ``"seconds"``.
        granularity: ``"word"`` or ``"segment"``.
        words: Word-level timings.
        segments: Segment-level timings.
    """

    unit: str
    granularity: str
    words: list[WordTiming] = field(default_factory=list)
    segments: list[SegmentTiming] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    """Result returned by `KhayaClient.transcribe()` and `KhayaClient.atranscribe()`.

    Attributes:
        text: The transcribed string.
        language: Language code of the transcribed audio (e.g. ``"twi"``).
        warnings: Advisories from the API, such as a notice that the language
            code you sent is a deprecated legacy form. Empty on ASR v1, which
            returns no structured body.
        timings: Alignment data when ``timestamps`` was requested, else None.
        usage: Credit cost and rate limit headers from the response, or None
            if the gateway sent none.
    """

    text: str
    language: str
    warnings: list[str] = field(default_factory=list)
    timings: Timings | None = None
    usage: Usage | None = field(default=None, compare=False)


@dataclass
class SynthesisResult:
    """Result returned by `KhayaClient.synthesize()` and `KhayaClient.asynthesize()`.

    Attributes:
        audio: Raw audio bytes.
        language: Language code used for synthesis (e.g. ``"tw"``).
        usage: Credit cost and rate limit headers from the response, or None
            if the gateway sent none.
    """

    audio: bytes
    language: str
    usage: Usage | None = field(default=None, compare=False)

    def save(self, path: str) -> None:
        """Write the audio bytes to a file.

        Args:
            path: Destination file path (e.g. ``"output.wav"``). The parent
                directory must exist.

        Raises:
            TTSGenerationError: If the destination cannot be written.
        """
        try:
            with open(path, "wb") as f:
                f.write(self.audio)
        except OSError as e:
            parent = os.path.dirname(os.path.abspath(path))
            hint = "" if os.path.isdir(parent) else f" (no such directory: {parent})"
            raise TTSGenerationError(f"Could not write audio to {path!r}{hint}", 400) from e
