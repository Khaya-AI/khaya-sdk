import logging
import mimetypes
import os
import warnings
from typing import Any, BinaryIO, Literal

import httpx

from khaya.exceptions import ASRTranscriptionError
from khaya.models import SegmentTiming, Timings, TranscriptionResult, Usage, WordTiming
from khaya.services.base_api import BaseApi, decode_json
from khaya.utils import check_authentication

logger = logging.getLogger(__name__)

Granularity = Literal["word", "segment"]

# A path, the audio itself, or a file object opened in binary mode.
AudioInput = str | os.PathLike[str] | bytes | bytearray | memoryview | BinaryIO


def _content_type(audio_file_path: str) -> str:
    """Pick the upload Content-Type from the file extension.

    The gateway accepts only ``audio/*``, ``video/*`` and
    ``application/octet-stream`` (anything else is a 415), so an extension that
    maps to some other type, or to none, falls back to the octet-stream.
    """
    guessed, _ = mimetypes.guess_type(audio_file_path)
    if guessed is not None and guessed.startswith(("audio/", "video/")):
        return guessed
    return "application/octet-stream"


def _read_audio(audio_file_path: str) -> bytes:
    try:
        with open(audio_file_path, "rb") as audio_file:
            data = audio_file.read()
    except FileNotFoundError as e:
        raise ASRTranscriptionError(f"Audio file not found: {audio_file_path}", 400) from e
    logger.debug("Loaded %d bytes from audio file", len(data))
    return data


def _load_audio(audio: AudioInput | None, audio_file_path: str | None) -> tuple[bytes, str]:
    """Return the audio bytes and the Content-Type to upload them with."""
    if audio_file_path is not None:
        warnings.warn(
            "audio_file_path is deprecated; pass the path as the first argument (audio)",
            DeprecationWarning,
            stacklevel=5,
        )
        if audio is not None:
            raise ASRTranscriptionError("Pass audio or audio_file_path, not both", 400)
        audio = audio_file_path

    name: object = None
    if isinstance(audio, bytes | bytearray | memoryview):
        data = bytes(audio)
    elif isinstance(audio, str | os.PathLike):
        name = os.fspath(audio)
        data = _read_audio(name)
    else:
        read = getattr(audio, "read", None)
        if read is None:
            raise ASRTranscriptionError(
                f"audio must be a path, bytes or a binary file object, got {type(audio).__name__}",
                400,
            )
        data = read()
        if not isinstance(data, bytes):
            raise ASRTranscriptionError("Audio file object must be opened in binary mode", 400)
        name = getattr(audio, "name", None)
    # An empty upload is billed and transcribes to nothing.
    if not data:
        raise ASRTranscriptionError("Audio is empty", 400)
    # Bytes carry no file name, so they go up as an octet-stream.
    return data, _content_type(name if isinstance(name, str) else "")


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

    The API returns ``{"text": ..., "warnings": [...], "timings": {...}}``; a
    bare JSON string is also accepted and carries neither warnings nor timings.
    """
    body = decode_json(response)
    usage = Usage.from_headers(response.headers)
    if isinstance(body, str):
        return TranscriptionResult(text=body, language=language, usage=usage)

    warnings = list(body.get("warnings", []))
    for warning in warnings:
        logger.warning("API advisory: %s", warning)
    return TranscriptionResult(
        text=body.get("text", ""),
        language=language,
        warnings=warnings,
        timings=_timings(body.get("timings")),
        usage=usage,
    )


class AsrService:
    def __init__(self, http_client: BaseApi) -> None:
        self.http_client = http_client
        self.endpoint = http_client.config.endpoints["asr"]

    @check_authentication
    def transcribe(
        self,
        audio: AudioInput | None = None,
        language: str = "twi",
        timestamps: Granularity | None = None,
        *,
        timeout: float | None = None,
        audio_file_path: str | None = None,
    ) -> TranscriptionResult:
        """Convert speech to text from an audio file.

        Args:
            audio: Path to the audio file, the audio as bytes, or a file
                object opened in binary mode.
            language: The spoken language code (e.g. ``"twi"`` for Twi).
            timestamps: Request alignment data — ``"word"`` or ``"segment"``.
            timeout: Seconds to wait for this call, overriding
                ``Settings.timeout``.
            audio_file_path: Deprecated name for a path passed as ``audio``.

        Returns:
            TranscriptionResult with the transcribed text, any API warnings,
            and timings when requested.

        Raises:
            ASRTranscriptionError: If the file does not exist, the audio is
                empty, or timestamps is not a valid granularity.
            AuthenticationError: If no API key is configured.
            APIError: On HTTP errors from the API.
        """
        params = _params(language, timestamps)
        logger.debug("Transcribing audio (language=%s, timestamps=%s)", language, timestamps)
        data, content_type = _load_audio(audio, audio_file_path)
        response: httpx.Response = self.http_client.request(
            "POST",
            self.endpoint,
            params=params,
            content=data,
            headers={"Content-Type": content_type},
            timeout=timeout,
        )
        return _to_result(response, language)

    @check_authentication
    async def atranscribe(
        self,
        audio: AudioInput | None = None,
        language: str = "twi",
        timestamps: Granularity | None = None,
        *,
        timeout: float | None = None,
        audio_file_path: str | None = None,
    ) -> TranscriptionResult:
        """Async version of transcribe."""
        params = _params(language, timestamps)
        logger.debug("Transcribing audio (language=%s, timestamps=%s)", language, timestamps)
        data, content_type = _load_audio(audio, audio_file_path)
        response: httpx.Response = await self.http_client.arequest(
            "POST",
            self.endpoint,
            params=params,
            content=data,
            headers={"Content-Type": content_type},
            timeout=timeout,
        )
        return _to_result(response, language)
