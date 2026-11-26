from khaya.config import Settings
from khaya.models import SynthesisResult, TranscriptionResult, TranslationResult
from khaya.services.asr import AsrService, AudioInput, Granularity
from khaya.services.base_api import BaseApi
from khaya.services.translation import TranslationService
from khaya.services.tts import TtsService


class KhayaClient:
    """High-level interface to the Khaya API.

    Provides translation, automatic speech recognition (ASR), and
    text-to-speech (TTS) for African languages.

    Args:
        api_key: Your Khaya API key. Defaults to the ``KHAYA_API_KEY``
            environment variable.
        config: Optional pre-built Settings instance. When provided,
            ``api_key`` is ignored.

    Example::

        from khaya import KhayaClient

        with KhayaClient() as khaya:  # reads KHAYA_API_KEY
            result = khaya.translate("Hello", "en-tw")
            print(result.text)

    Async example::

        async with KhayaClient(api_key) as khaya:
            result = await khaya.atranslate("Hello", "en-tw")
            print(result.text)
    """

    def __init__(
        self,
        api_key: str | None = None,
        config: Settings | None = None,
    ) -> None:
        if config is None:
            # Settings(api_key=None) would override KHAYA_API_KEY.
            config = Settings(api_key=api_key) if api_key is not None else Settings()
        self.config = config
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

    def translate(
        self, text: str, language_pair: str = "en-tw", *, timeout: float | None = None
    ) -> TranslationResult:
        """Translate text from one language to another.

        Args:
            text: The text to translate.
            language_pair: Source-target language pair (e.g. ``"en-tw"``).
            timeout: Seconds to wait for this call, overriding
                ``Settings.timeout``.

        Returns:
            TranslationResult with ``.text``, ``.source_language``, and ``.target_language``.
        """
        return self.translation.translate(text, language_pair, timeout=timeout)

    def transcribe(
        self,
        audio: AudioInput | None = None,
        language: str = "twi",
        timestamps: Granularity | None = None,
        *,
        timeout: float | None = None,
        audio_file_path: str | None = None,
    ) -> TranscriptionResult:
        """Transcribe an audio file to text.

        Args:
            audio: Path to the audio file, the audio as bytes, or a file
                object opened in binary mode.
            language: Language spoken in the audio (e.g. ``"twi"`` for Twi).
            timestamps: Request alignment data — ``"word"`` or ``"segment"``.
            timeout: Seconds to wait for this call, overriding
                ``Settings.timeout``.

        Returns:
            TranscriptionResult with ``.text``, ``.language``, ``.warnings``,
            and ``.timings`` when requested.
        """
        return self.asr.transcribe(
            audio, language, timestamps, timeout=timeout, audio_file_path=audio_file_path
        )

    def synthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
        *,
        timeout: float | None = None,
    ) -> SynthesisResult:
        """Synthesize speech from text.

        Args:
            text: The text to convert to speech.
            language: Target language code (e.g. ``"twi"`` for Asante Twi).
            speaker: Optional speaker voice — ``"male_low"``, ``"male_high"``,
                or ``"female"``.
            timeout: Seconds to wait for this call, overriding
                ``Settings.timeout``.

        Returns:
            SynthesisResult with ``.audio`` bytes and a ``.save(path)`` helper.
        """
        return self.tts.synthesize(text, language, speaker, timeout=timeout)

    # --- Async API ---

    async def atranslate(
        self, text: str, language_pair: str = "en-tw", *, timeout: float | None = None
    ) -> TranslationResult:
        """Async version of `translate()`."""
        return await self.translation.atranslate(text, language_pair, timeout=timeout)

    async def atranscribe(
        self,
        audio: AudioInput | None = None,
        language: str = "twi",
        timestamps: Granularity | None = None,
        *,
        timeout: float | None = None,
        audio_file_path: str | None = None,
    ) -> TranscriptionResult:
        """Async version of `transcribe()`."""
        return await self.asr.atranscribe(
            audio, language, timestamps, timeout=timeout, audio_file_path=audio_file_path
        )

    async def asynthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
        *,
        timeout: float | None = None,
    ) -> SynthesisResult:
        """Async version of `synthesize()`."""
        return await self.tts.asynthesize(text, language, speaker, timeout=timeout)
