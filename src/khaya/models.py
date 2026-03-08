from dataclasses import dataclass


@dataclass
class TranslationResult:
    """Result returned by :meth:`~khaya.KhayaClient.translate` and :meth:`~khaya.KhayaClient.atranslate`.

    Attributes:
        text: The translated string.
        source_language: Source language code (e.g. ``"en"``).
        target_language: Target language code (e.g. ``"tw"``).
    """

    text: str
    source_language: str
    target_language: str


@dataclass
class TranscriptionResult:
    """Result returned by :meth:`~khaya.KhayaClient.transcribe` and :meth:`~khaya.KhayaClient.atranscribe`.

    Attributes:
        text: The transcribed string.
        language: Language code of the transcribed audio (e.g. ``"tw"``).
    """

    text: str
    language: str


@dataclass
class SynthesisResult:
    """Result returned by :meth:`~khaya.KhayaClient.synthesize` and :meth:`~khaya.KhayaClient.asynthesize`.

    Attributes:
        audio: Raw audio bytes.
        language: Language code used for synthesis (e.g. ``"tw"``).
    """

    audio: bytes
    language: str

    def save(self, path: str) -> None:
        """Write the audio bytes to a file.

        Args:
            path: Destination file path (e.g. ``"output.wav"``).
        """
        with open(path, "wb") as f:
            f.write(self.audio)
