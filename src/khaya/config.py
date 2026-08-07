from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from khaya.constants import RETRY_ATTEMPTS, TIMEOUT


class Settings(BaseSettings):
    """Runtime configuration for `KhayaClient`.

    Every field can be supplied directly or through a ``KHAYA_``-prefixed
    environment variable — ``KHAYA_API_KEY``, ``KHAYA_BASE_URL``,
    ``KHAYA_TIMEOUT``, ``KHAYA_RETRY_ATTEMPTS``. Unprefixed names are ignored.

    Invalid values raise ``ValidationError`` at construction time rather than
    at the first request.

    Attributes:
        api_key: Khaya API subscription key, sent as the
            ``Ocp-Apim-Subscription-Key`` header. Defaults to ``None``.
        base_url: API root. Must be HTTPS, since the key is sent on every
            request. Defaults to ``https://translation-api.ghananlp.org``.
        timeout: Per-request timeout in seconds; must be ``> 0``. Defaults
            to ``30``.
        retry_attempts: Total HTTP attempts per request, including the
            first; must be ``>= 1``. Defaults to ``3``.

    Example::

        from khaya.config import Settings

        config = Settings(api_key="...", timeout=60, retry_attempts=5)
    """

    api_key: str | None = Field(
        default=None,
        description="Khaya API subscription key. Sent as the Ocp-Apim-Subscription-Key header.",
    )
    base_url: str = Field(
        default="https://translation-api.ghananlp.org",
        description="API root. Must be HTTPS — the API key is sent on every request.",
    )
    timeout: int = Field(default=TIMEOUT, gt=0, description="Per-request timeout in seconds.")
    retry_attempts: int = Field(
        default=RETRY_ATTEMPTS,
        ge=1,
        # At least one attempt: retry_attempts=0 would skip the request entirely.
        description="Total HTTP attempts per request, including the first.",
    )

    # env_prefix, not a per-field validation_alias. Without the prefix these
    # fields bind to bare BASE_URL/TIMEOUT/RETRY_ATTEMPTS, so a user whose
    # environment already sets BASE_URL for their own app would silently send
    # their API key and request bodies to that host.
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
