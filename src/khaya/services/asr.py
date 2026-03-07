import httpx

from khaya.exceptions import ASRTranscriptionError
from khaya.services.base_api import BaseApi
from khaya.utils import check_authentication


class AsrService:
    def __init__(self, http_client: BaseApi) -> None:
        self.http_client = http_client
        self.endpoint = http_client.config.endpoints["asr"]

    @check_authentication
    def transcribe(
        self, audio_file_path: str, language: str = "tw"
    ) -> httpx.Response:
        """Convert speech to text from an audio file.

        Args:
            audio_file_path: Path to the audio file (.wav).
            language: The spoken language code (e.g. "tw" for Twi).

        Returns:
            httpx.Response containing the transcribed text.

        Raises:
            ASRTranscriptionError: If the file does not exist.
            AuthenticationError: If no API key is configured.
            APIError: On HTTP errors from the API.
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                data = audio_file.read()
        except FileNotFoundError as e:
            raise ASRTranscriptionError(
                f"Audio file not found: {audio_file_path}", 400
            ) from e

        return self.http_client.request(
            "POST", self.endpoint, params={"language": language}, content=data
        )

    @check_authentication
    async def atranscribe(
        self, audio_file_path: str, language: str = "tw"
    ) -> httpx.Response:
        """Async version of transcribe."""
        try:
            with open(audio_file_path, "rb") as audio_file:
                data = audio_file.read()
        except FileNotFoundError as e:
            raise ASRTranscriptionError(
                f"Audio file not found: {audio_file_path}", 400
            ) from e

        return await self.http_client.arequest(
            "POST", self.endpoint, params={"language": language}, content=data
        )
