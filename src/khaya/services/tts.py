import logging

import httpx

from khaya.constants import SUPPORTED_TTS_LANGUAGES
from khaya.exceptions import TTSGenerationError
from khaya.models import SynthesisResult
from khaya.services.base_api import BaseApi
from khaya.utils import check_authentication, warn_if_unknown

logger = logging.getLogger(__name__)


class TtsService:
    def __init__(self, http_client: BaseApi) -> None:
        self.http_client = http_client
        self.endpoint = http_client.config.endpoints["tts"]

    @check_authentication
    def synthesize(self, text: str, language: str) -> SynthesisResult:
        """Convert text to speech in an African language.

        Args:
            text: The text to synthesize.
            language: The language code (e.g. ``"tw"`` for Twi).

        Returns:
            SynthesisResult with raw audio bytes and a save() helper.

        Raises:
            TTSGenerationError: If text or language are empty.
            AuthenticationError: If no API key is configured.
            APIError: On HTTP errors from the API.
        """
        if not text or not language:
            raise TTSGenerationError("Text and language are required", 400)
        warn_if_unknown(language, SUPPORTED_TTS_LANGUAGES, "TTS language")
        logger.debug("Synthesizing %d chars (language=%s)", len(text), language)
        response: httpx.Response = self.http_client.request(
            "POST", self.endpoint, json={"text": text, "language": language}
        )
        result = SynthesisResult(audio=response.content, language=language)
        logger.debug("Synthesis complete: %d audio bytes (language=%s)", len(result.audio), language)
        return result

    @check_authentication
    async def asynthesize(self, text: str, language: str) -> SynthesisResult:
        """Async version of synthesize."""
        if not text or not language:
            raise TTSGenerationError("Text and language are required", 400)
        warn_if_unknown(language, SUPPORTED_TTS_LANGUAGES, "TTS language")
        logger.debug("Synthesizing %d chars (language=%s)", len(text), language)
        response: httpx.Response = await self.http_client.arequest(
            "POST", self.endpoint, json={"text": text, "language": language}
        )
        result = SynthesisResult(audio=response.content, language=language)
        logger.debug("Synthesis complete: %d audio bytes (language=%s)", len(result.audio), language)
        return result
