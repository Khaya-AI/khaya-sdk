import logging
from typing import Any, Literal

import httpx

from khaya.exceptions import ASRTranscriptionError
from khaya.models import SegmentTiming, Timings, TranscriptionResult, WordTiming
from khaya.services.base_api import BaseApi, decode_json
from khaya.utils import check_authentication

logger = logging.getLogger(__name__)

Granularity = Literal["word", "segment"]


def _read_audio(audio_file_path: str) -> bytes:
    try:
        with open(audio_file_path, "rb") as audio_file:
            data = audio_file.read()
    except FileNotFoundError as e:
        raise ASRTranscriptionError(f"Audio file not found: {audio_file_path}", 400) from e
    logger.debug("Loaded %d bytes from audio file", len(data))
    return data


def _params(language: str, timestamps: Granularity | None) -> dict[str, str]:
    if timestamps is not None and timestamps not in ("word", "segment"):
        raise ASRTranscriptionError(
            f"timestamps must be 'word' or 'segment', got {timestamps!r}", 400
        )
    params = {"language": language}
    if timestamps is not None:
        params["timestamps"] = timestamps
    return params


def _timings(raw: dict[str, Any] | None) -> Timings | None:
    if not raw:
        return None
    return Timings(
        unit=raw.get("unit", "seconds"),
        granularity=raw.get("granularity", ""),
        words=[WordTiming(**w) for w in raw.get("words", [])],
        segments=[SegmentTiming(**s) for s in raw.get("segments", [])],
    )


def _to_result(response: httpx.Response, language: str) -> TranscriptionResult:
    """Build a result from either shape the API returns.

    v3 and v2 return ``{"text": ..., "warnings": [...], "timings": {...}}``;
    v1 returns a bare JSON string, so it can carry neither.
    """
    body = decode_json(response)
    if isinstance(body, str):
        return TranscriptionResult(text=body, language=language)

    warnings = list(body.get("warnings", []))
    for warning in warnings:
        logger.warning("API advisory: %s", warning)
    return TranscriptionResult(
        text=body.get("text", ""),
        language=language,
        warnings=warnings,
        timings=_timings(body.get("timings")),
    )


class AsrService:
    def __init__(self, http_client: BaseApi) -> None:
        self.http_client = http_client
        self.endpoint = http_client.config.endpoints["asr"]

    @check_authentication
    def transcribe(
        self,
        audio_file_path: str,
        language: str = "twi",
        timestamps: Granularity | None = None,
    ) -> TranscriptionResult:
        """Convert speech to text from an audio file.

        Args:
            audio_file_path: Path to the audio file (.wav).
            language: The spoken language code (e.g. ``"twi"`` for Twi).
            timestamps: Request alignment data — ``"word"`` or ``"segment"``.
                Requires ASR v2 or later.

        Returns:
            TranscriptionResult with the transcribed text, any API warnings,
            and timings when requested.

        Raises:
            ASRTranscriptionError: If the file does not exist or timestamps is
                not a valid granularity.
            AuthenticationError: If no API key is configured.
            APIError: On HTTP errors from the API.
        """
        params = _params(language, timestamps)
        logger.debug("Transcribing audio file (language=%s, timestamps=%s)", language, timestamps)
        data = _read_audio(audio_file_path)
        response: httpx.Response = self.http_client.request(
            "POST", self.endpoint, params=params, content=data
        )
        return _to_result(response, language)

    @check_authentication
    async def atranscribe(
        self,
        audio_file_path: str,
        language: str = "twi",
        timestamps: Granularity | None = None,
    ) -> TranscriptionResult:
        """Async version of transcribe."""
        params = _params(language, timestamps)
        logger.debug("Transcribing audio file (language=%s, timestamps=%s)", language, timestamps)
        data = _read_audio(audio_file_path)
        response: httpx.Response = await self.http_client.arequest(
            "POST", self.endpoint, params=params, content=data
        )
        return _to_result(response, language)
