
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from khaya.constants import RETRY_ATTEMPTS, TIMEOUT


class Settings(BaseSettings):
    api_key: str | None = Field(default=None)
    base_url: str = "https://translation.ghananlp.org"
    timeout: int = TIMEOUT
    retry_attempts: int = RETRY_ATTEMPTS

    model_config = SettingsConfigDict(
        env_file=None, extra="forbid", populate_by_name=True
    )

    @field_validator("base_url")
    @classmethod
    def validate_https(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError(f"base_url must use HTTPS, got: {v!r}")
        return v

    @property
    def endpoints(self) -> dict[str, str]:
        return {
            "translation": f"{self.base_url}/v1/translate",
            "tts": f"{self.base_url}/tts/v1/tts",
            "asr": f"{self.base_url}/asr/v1/transcribe",
        }


class DevSettings(Settings):
    """Development settings: automatically load from a .env file."""

    api_key: str | None = Field(default=None, alias="KHAYA_API_KEY")
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="forbid"
    )
