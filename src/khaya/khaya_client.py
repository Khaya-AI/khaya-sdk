
import httpx

from khaya.config import Settings
from khaya.services.asr import AsrService
from khaya.services.base_api import BaseApi
from khaya.services.translation import TranslationService
from khaya.services.tts import TtsService

__version__ = "0.1.0"


class KhayaClient:
    """High-level interface to the Khaya API.

    Provides translation, automatic speech recognition (ASR), and
    text-to-speech (TTS) for African languages.

    Args:
        api_key: Your Khaya API key. Can also be set via the
            ``KHAYA_API_KEY`` environment variable.
        config: Optional pre-built Settings instance. When provided,
            ``api_key`` is ignored.

    Example::

        import os
        from khaya import KhayaClient

        with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
            result = khaya.translate("Hello", "en-tw")
            print(result.json())

    Async example::

        async with KhayaClient(api_key) as khaya:
            result = await khaya.atranslate("Hello", "en-tw")
    """

    def __init__(
        self,
        api_key: str,
        config: Settings | None = None,
    ) -> None:
        self.config = config if config else Settings(api_key=api_key)
        self.http_client = BaseApi(self.config)
        self.translation = TranslationService(self.http_client)
        self.asr = AsrService(self.http_client)
        self.tts = TtsService(self.http_client)

    # --- Sync context manager ---

    def __enter__(self) -> "KhayaClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.http_client.close()

    # --- Async context manager ---

    async def __aenter__(self) -> "KhayaClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.http_client.aclose()

    # --- Sync API ---

    def translate(self, text: str, language_pair: str = "en-tw") -> httpx.Response:
        """Translate text from one language to another.

        Args:
            text: The text to translate.
            language_pair: Source-target language pair (e.g. ``"en-tw"``).

        Returns:
            httpx.Response — call ``.json()`` for the translated string.
        """
        return self.translation.translate(text, language_pair)

    def transcribe(self, audio_file_path: str, language: str = "tw") -> httpx.Response:
        """Transcribe an audio file to text.

        Args:
            audio_file_path: Path to the .wav audio file.
            language: Language spoken in the audio (e.g. ``"tw"`` for Twi).

        Returns:
            httpx.Response — call ``.json()`` for the transcribed string.
        """
        return self.asr.transcribe(audio_file_path, language)

    def synthesize(self, text: str, language: str) -> httpx.Response:
        """Synthesize speech from text.

        Args:
            text: The text to convert to speech.
            language: Target language code (e.g. ``"tw"`` for Twi).

        Returns:
            httpx.Response — use ``.content`` for the raw audio bytes.
        """
        return self.tts.synthesize(text, language)

    # --- Async API ---

    async def atranslate(
        self, text: str, language_pair: str = "en-tw"
    ) -> httpx.Response:
        """Async version of :meth:`translate`."""
        return await self.translation.atranslate(text, language_pair)

    async def atranscribe(
        self, audio_file_path: str, language: str = "tw"
    ) -> httpx.Response:
        """Async version of :meth:`transcribe`."""
        return await self.asr.atranscribe(audio_file_path, language)

    async def asynthesize(self, text: str, language: str) -> httpx.Response:
        """Async version of :meth:`synthesize`."""
        return await self.tts.asynthesize(text, language)
