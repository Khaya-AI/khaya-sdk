import logging

import httpx

from khaya.exceptions import TTSGenerationError
from khaya.models import SynthesisResult
from khaya.services.base_api import BaseApi
from khaya.utils import check_authentication

logger = logging.getLogger(__name__)


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
            TTSGenerationError: If text or language are empty.
            AuthenticationError: If no API key is configured.
            APIError: On HTTP errors from the API.
        """
        if not text or not language:
            raise TTSGenerationError("Text and language are required", 400)
        logger.debug(
            "Synthesizing %d chars (language=%s, speaker=%s)",
            len(text),
            language,
            speaker,
        )
        payload: dict = {"text": text, "language": language}
        if speaker is not None:
            payload["speaker"] = speaker
        response: httpx.Response = self.http_client.request("POST", self.endpoint, json=payload)
        result = SynthesisResult(audio=response.content, language=language)
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
        if not text or not language:
            raise TTSGenerationError("Text and language are required", 400)
        logger.debug(
            "Synthesizing %d chars (language=%s, speaker=%s)",
            len(text),
            language,
            speaker,
        )
        payload: dict = {"text": text, "language": language}
        if speaker is not None:
            payload["speaker"] = speaker
        response: httpx.Response = await self.http_client.arequest(
            "POST", self.endpoint, json=payload
        )
        result = SynthesisResult(audio=response.content, language=language)
        logger.debug(
            "Synthesis complete: %d audio bytes (language=%s)",
            len(result.audio),
            language,
        )
        return result
