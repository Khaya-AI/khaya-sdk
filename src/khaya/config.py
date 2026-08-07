from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from khaya.constants import RETRY_ATTEMPTS, TIMEOUT

TranslationVersion = Literal["v1", "v2"]
AsrVersion = Literal["v1", "v2", "v3"]
TtsVersion = Literal["v1", "v2"]

# Paths per (service, version). A version is not a substitutable string: TTS
# renamed its route between v1 and v2, so f"/tts/{version}/tts" 404s on v2.
API_ENDPOINTS: dict[tuple[str, str], str] = {
    ("translation", "v1"): "/v1/translate",
    ("translation", "v2"): "/v2/translate",
    ("asr", "v1"): "/asr/v1/transcribe",
    ("asr", "v2"): "/asr/v2/transcribe",
    ("asr", "v3"): "/asr/v3/transcribe",
    ("tts", "v1"): "/tts/v1/tts",
    ("tts", "v2"): "/tts/v2/synthesize",
}


class Settings(BaseSettings):
    """Runtime configuration for `KhayaClient`.

    Each field also reads a ``KHAYA_``-prefixed environment variable
    (``KHAYA_API_KEY``, ``KHAYA_BASE_URL``, ...).

    Attributes:
        api_key: Sent as the ``Ocp-Apim-Subscription-Key`` header.
        base_url: API root. Must be HTTPS.
        timeout: Per-request timeout in seconds.
        retry_attempts: Total attempts per request, including the first.
        translation_version: Which translation API version to call. ``v2`` is
            identical to ``v1`` in request shape, latency and output.
        asr_version: Which ASR API version to call. ``v1`` returns a bare
            string and supports neither warnings nor timestamps.
        tts_version: Which TTS API version to call. ``v2`` serves the same
            audio from a different route.
    """

    api_key: str | None = Field(default=None)
    base_url: str = "https://translation-api.ghananlp.org"
    timeout: int = Field(default=TIMEOUT, gt=0)
    # retry_attempts=0 would skip the request entirely.
    retry_attempts: int = Field(default=RETRY_ATTEMPTS, ge=1)
    # Defaults are pinned, not discovered: the API publishes no capability
    # endpoint, and response shapes differ between versions (ASR v1 returns a
    # bare string, v3 an object). Silent drift would change parsing under
    # callers with no release.
    translation_version: TranslationVersion = "v1"
    # v3 is the one newer version that earns the switch — same latency as v1,
    # but warnings and optional word/segment timings.
    asr_version: AsrVersion = "v3"
    tts_version: TtsVersion = "v1"

    # Prefixed, so a BASE_URL set for an unrelated app cannot redirect the
    # API key to another host.
    model_config = SettingsConfigDict(env_file=None, extra="forbid", env_prefix="KHAYA_")

    @field_validator("base_url")
    @classmethod
    def base_url_must_use_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("HTTPS is required for base_url")
        return v

    @property
    def endpoints(self) -> dict[str, str]:
        """Resolve each service to a full URL for its configured version."""
        selected = (
            ("translation", self.translation_version),
            ("asr", self.asr_version),
            ("tts", self.tts_version),
        )
        return {
            service: f"{self.base_url}{API_ENDPOINTS[(service, version)]}"
            for service, version in selected
        }


class DevSettings(Settings):
    """`Settings` that also reads a local ``.env`` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="forbid", env_prefix="KHAYA_")
