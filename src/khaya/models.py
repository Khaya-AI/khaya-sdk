from dataclasses import dataclass, field


@dataclass
class TranslationResult:
    """Result returned by `KhayaClient.translate()` and `KhayaClient.atranslate()`.

    Attributes:
        text: The translated string.
        source_language: Source language code (e.g. ``"en"``).
        target_language: Target language code (e.g. ``"tw"``).
    """

    text: str
    source_language: str
    target_language: str


@dataclass
class WordTiming:
    """When a single word was spoken.

    Attributes:
        word: The word as transcribed.
        start: Start offset in seconds.
        end: End offset in seconds.
    """

    word: str
    start: float
    end: float


@dataclass
class SegmentTiming:
    """When a contiguous span of speech was spoken.

    Attributes:
        text: The segment as transcribed.
        start: Start offset in seconds.
        end: End offset in seconds.
    """

    text: str
    start: float
    end: float


@dataclass
class Timings:
    """Alignment data, present only when ``timestamps`` was requested.

    Exactly one of ``words`` or ``segments`` is populated, matching the
    requested granularity.

    Attributes:
        unit: Unit of the offsets, currently always ``"seconds"``.
        granularity: ``"word"`` or ``"segment"``.
        words: Word-level timings.
        segments: Segment-level timings.
    """

    unit: str
    granularity: str
    words: list[WordTiming] = field(default_factory=list)
    segments: list[SegmentTiming] = field(default_factory=list)


@dataclass
class TranscriptionResult:
    """Result returned by `KhayaClient.transcribe()` and `KhayaClient.atranscribe()`.

    Attributes:
        text: The transcribed string.
        language: Language code of the transcribed audio (e.g. ``"twi"``).
        warnings: Advisories from the API, such as a notice that the language
            code you sent is a deprecated legacy form. Empty on ASR v1, which
            returns no structured body.
        timings: Alignment data when ``timestamps`` was requested, else None.
    """

    text: str
    language: str
    warnings: list[str] = field(default_factory=list)
    timings: Timings | None = None


@dataclass
class SynthesisResult:
    """Result returned by `KhayaClient.synthesize()` and `KhayaClient.asynthesize()`.

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
