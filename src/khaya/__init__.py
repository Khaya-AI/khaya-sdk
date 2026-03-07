from importlib.metadata import version

from .exceptions import (
    APIError,
    ASRTranscriptionError,
    AuthenticationError,
    RateLimitError,
    TranslationError,
    TTSGenerationError,
)
from .khaya_client import KhayaClient

__version__ = version("khaya")

__all__ = [
    "KhayaClient",
    "__version__",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "TranslationError",
    "TTSGenerationError",
    "ASRTranscriptionError",
]
