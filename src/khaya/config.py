from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from khaya.constants import RETRY_ATTEMPTS, TIMEOUT

# Route of each service on the Khaya platform. The platform publishes a single
# API version, ``v1``, for every service, so there is nothing to select.
API_ENDPOINTS: dict[str, str] = {
    "translation": "/translate/v1/translate",
    "asr": "/asr/v1/transcribe",
    "tts": "/tts/v1/synthesize",
}


class Settings(BaseSettings):
    """Runtime configuration for `KhayaClient`.

    Each field also reads a ``KHAYA_``-prefixed environment variable
    (``KHAYA_API_KEY``, ``KHAYA_BASE_URL``, ...).

    Attributes:
        api_key: Sent as an ``Authorization: Bearer`` token.
        base_url: API root. Must be HTTPS.
        timeout: Per-request timeout in seconds.
        retry_attempts: Total attempts per request, including the first.
    """

    api_key: str | None = Field(default=None)
    base_url: str = "https://api.khaya.ai"
    timeout: int = Field(default=TIMEOUT, gt=0)
    # retry_attempts=0 would skip the request entirely.
    retry_attempts: int = Field(default=RETRY_ATTEMPTS, ge=1)
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
        """Resolve each service to its full URL."""
        base_url = self.base_url.rstrip("/")
        return {service: f"{base_url}{path}" for service, path in API_ENDPOINTS.items()}


class DevSettings(Settings):
    """`Settings` that also reads a local ``.env`` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="forbid", env_prefix="KHAYA_")
