import httpx

from khaya.exceptions import TTSGenerationError
from khaya.services.base_api import BaseApi
from khaya.utils import check_authentication


class TtsService:
    def __init__(self, http_client: BaseApi) -> None:
        self.http_client = http_client
        self.endpoint = http_client.config.endpoints["tts"]

    @check_authentication
    def synthesize(self, text: str, language: str) -> httpx.Response:
        """Convert text to speech in an African language.

        Args:
            text: The text to synthesize.
            language: The language code (e.g. "tw" for Twi).

        Returns:
            httpx.Response whose .content is the audio bytes.

        Raises:
            TTSGenerationError: If text or language are empty.
            AuthenticationError: If no API key is configured.
            APIError: On HTTP errors from the API.
        """
        if not text or not language:
            raise TTSGenerationError("Text and language are required", 400)
        payload = {"text": text, "language": language}
        return self.http_client.request("POST", self.endpoint, json=payload)

    @check_authentication
    async def asynthesize(self, text: str, language: str) -> httpx.Response:
        """Async version of synthesize."""
        if not text or not language:
            raise TTSGenerationError("Text and language are required", 400)
        payload = {"text": text, "language": language}
        return await self.http_client.arequest("POST", self.endpoint, json=payload)
