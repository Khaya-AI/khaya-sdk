import logging

import httpx

from khaya.constants import SUPPORTED_ASR_LANGUAGES
from khaya.exceptions import ASRTranscriptionError
from khaya.models import TranscriptionResult
from khaya.services.base_api import BaseApi
from khaya.utils import check_authentication, warn_if_unknown

logger = logging.getLogger(__name__)


class AsrService:
    def __init__(self, http_client: BaseApi) -> None:
        self.http_client = http_client
        self.endpoint = http_client.config.endpoints["asr"]

    @check_authentication
    def transcribe(
        self, audio_file_path: str, language: str = "tw"
    ) -> TranscriptionResult:
        """Convert speech to text from an audio file.

        Args:
            audio_file_path: Path to the audio file (.wav).
            language: The spoken language code (e.g. ``"tw"`` for Twi).

        Returns:
            TranscriptionResult with the transcribed text and language code.

        Raises:
            ASRTranscriptionError: If the file does not exist.
            AuthenticationError: If no API key is configured.
            APIError: On HTTP errors from the API.
        """
        warn_if_unknown(language, SUPPORTED_ASR_LANGUAGES, "ASR language")
        logger.debug("Transcribing audio file (language=%s)", language)
        try:
            with open(audio_file_path, "rb") as audio_file:
                data = audio_file.read()
        except FileNotFoundError as e:
            raise ASRTranscriptionError(
                f"Audio file not found: {audio_file_path}", 400
            ) from e
        logger.debug("Loaded %d bytes from audio file", len(data))
        response: httpx.Response = self.http_client.request(
            "POST", self.endpoint, params={"language": language}, content=data
        )
        return TranscriptionResult(text=response.json(), language=language)

    @check_authentication
    async def atranscribe(
        self, audio_file_path: str, language: str = "tw"
    ) -> TranscriptionResult:
        """Async version of transcribe."""
        warn_if_unknown(language, SUPPORTED_ASR_LANGUAGES, "ASR language")
        logger.debug("Transcribing audio file (language=%s)", language)
        try:
            with open(audio_file_path, "rb") as audio_file:
                data = audio_file.read()
        except FileNotFoundError as e:
            raise ASRTranscriptionError(
                f"Audio file not found: {audio_file_path}", 400
            ) from e
        logger.debug("Loaded %d bytes from audio file", len(data))
        response: httpx.Response = await self.http_client.arequest(
            "POST", self.endpoint, params={"language": language}, content=data
        )
        return TranscriptionResult(text=response.json(), language=language)
