import logging

import httpx

from khaya.constants import SUPPORTED_TTS_SPEAKERS
from khaya.exceptions import TTSGenerationError
from khaya.models import SynthesisResult, Usage
from khaya.services.base_api import BaseApi
from khaya.utils import check_authentication

logger = logging.getLogger(__name__)

# TTS never decodes JSON, so decode_json()'s non-JSON guard never runs here:
# without this, a gateway HTML error page served as a 200 is saved as a .wav.
_WAV_MAGIC = b"RIFF"


def _build_payload(text: str, language: str, speaker: str | None) -> dict:
    # .strip(): whitespace-only text is billed and returns invented speech.
    if not text.strip() or not language:
        raise TTSGenerationError("Text and language are required", 400)
    # Checked client-side to fail fast without a round trip; the API also
    # validates, returning INVALID_SPEAKER naming the accepted values.
    if speaker is not None and speaker not in SUPPORTED_TTS_SPEAKERS:
        raise TTSGenerationError(
            f"Unknown speaker {speaker!r}. Supported speakers: "
            f"{', '.join(sorted(SUPPORTED_TTS_SPEAKERS))}",
            400,
        )
    payload: dict = {"text": text, "language": language}
    if speaker is not None:
        # The wire field is speaker_id. Sending "speaker" is silently dropped:
        # the voice never changes and no error is raised.
        payload["speaker_id"] = speaker
    return payload


def _audio_from(response: httpx.Response, language: str) -> SynthesisResult:
    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("audio/") and not response.content.startswith(_WAV_MAGIC):
        snippet = " ".join(response.text.split())[:200]
        raise TTSGenerationError(
            f"Expected audio but received {content_type or 'an unknown content type'!r}: {snippet}",
            response.status_code,
        )
    return SynthesisResult(
        audio=response.content,
        language=language,
        usage=Usage.from_headers(response.headers),
    )


class TtsService:
    def __init__(self, http_client: BaseApi) -> None:
        self.http_client = http_client
        self.endpoint = http_client.config.endpoints["tts"]

    @check_authentication
    def synthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
    ) -> SynthesisResult:
        """Convert text to speech in an African language.

        Args:
            text: The text to synthesize.
            language: The language code (e.g. ``"twi"`` for Asante Twi).
            speaker: Optional speaker voice. One of ``"male_low"``,
                ``"male_high"``, or ``"female"``. Defaults to the API default
                when not provided.

        Returns:
            SynthesisResult with raw audio bytes and a save() helper.

        Raises:
            TTSGenerationError: If text or language are empty, if speaker is
                not a supported voice, or if the response body is not audio.
            AuthenticationError: If no API key is configured.
            APIError: On HTTP errors from the API.
        """
        payload = _build_payload(text, language, speaker)
        logger.debug(
            "Synthesizing %d chars (language=%s, speaker=%s)",
            len(text),
            language,
            speaker,
        )
        response: httpx.Response = self.http_client.request("POST", self.endpoint, json=payload)
        result = _audio_from(response, language)
        logger.debug(
            "Synthesis complete: %d audio bytes (language=%s)",
            len(result.audio),
            language,
        )
        return result

    @check_authentication
    async def asynthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
    ) -> SynthesisResult:
        """Async version of synthesize."""
        payload = _build_payload(text, language, speaker)
        logger.debug(
            "Synthesizing %d chars (language=%s, speaker=%s)",
            len(text),
            language,
            speaker,
        )
        response: httpx.Response = await self.http_client.arequest(
            "POST", self.endpoint, json=payload
        )
        result = _audio_from(response, language)
        logger.debug(
            "Synthesis complete: %d audio bytes (language=%s)",
            len(result.audio),
            language,
        )
        return result
