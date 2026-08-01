from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from khaya.constants import RETRY_ATTEMPTS, TIMEOUT


class Settings(BaseSettings):
    api_key: str | None = Field(default=None, validation_alias="KHAYA_API_KEY")
    base_url: str = "https://translation-api.ghananlp.org"
    timeout: int = Field(default=TIMEOUT, gt=0)
    # At least one attempt: retry_attempts=0 would skip the request entirely.
    retry_attempts: int = Field(default=RETRY_ATTEMPTS, ge=1)

    model_config = SettingsConfigDict(env_file=None, extra="forbid", populate_by_name=True)

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
    model_config = SettingsConfigDict(env_file=".env", extra="forbid", populate_by_name=True)
