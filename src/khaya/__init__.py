import logging
from importlib.metadata import version

from .constants import (
    SUPPORTED_ASR_LANGUAGES,
    SUPPORTED_LANGUAGE_PAIRS,
    SUPPORTED_TTS_LANGUAGES,
    SUPPORTED_TTS_SPEAKERS,
)
from .exceptions import (
    APIError,
    ASRTranscriptionError,
    AuthenticationError,
    RateLimitError,
    TranslationError,
    TTSGenerationError,
)
from .khaya_client import KhayaClient
from .models import SynthesisResult, TranscriptionResult, TranslationResult

__version__ = version("khaya")

# SDK logging convention: let the consuming application configure handlers.
logging.getLogger("khaya").addHandler(logging.NullHandler())

__all__ = [
    "KhayaClient",
    "__version__",
    # Result types
    "TranslationResult",
    "TranscriptionResult",
    "SynthesisResult",
    # Exceptions
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "TranslationError",
    "TTSGenerationError",
    "ASRTranscriptionError",
    # Reference data
    "SUPPORTED_LANGUAGE_PAIRS",
    "SUPPORTED_ASR_LANGUAGES",
    "SUPPORTED_TTS_LANGUAGES",
    "SUPPORTED_TTS_SPEAKERS",
]
