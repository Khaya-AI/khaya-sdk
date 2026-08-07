from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from khaya.constants import RETRY_ATTEMPTS, TIMEOUT


class Settings(BaseSettings):
    """Runtime configuration for `KhayaClient`.

    Each field also reads a ``KHAYA_``-prefixed environment variable
    (``KHAYA_API_KEY``, ``KHAYA_BASE_URL``, ...).

    Attributes:
        api_key: Sent as the ``Ocp-Apim-Subscription-Key`` header.
        base_url: API root. Must be HTTPS.
        timeout: Per-request timeout in seconds.
        retry_attempts: Total attempts per request, including the first.
    """

    api_key: str | None = Field(default=None)
    base_url: str = "https://translation-api.ghananlp.org"
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
        return {
            "translation": f"{self.base_url}/v1/translate",
            "asr": f"{self.base_url}/asr/v1/transcribe",
            "tts": f"{self.base_url}/tts/v1/tts",
        }


class DevSettings(Settings):
    """`Settings` that also reads a local ``.env`` file."""

    model_config = SettingsConfigDict(env_file=".env", extra="forbid", env_prefix="KHAYA_")
