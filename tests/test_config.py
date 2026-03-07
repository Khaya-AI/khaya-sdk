import pytest
from pydantic import ValidationError

from khaya.config import DevSettings, Settings
from khaya.constants import RETRY_ATTEMPTS, TIMEOUT


def test_default_config(monkeypatch):
    monkeypatch.delenv("KHAYA_API_KEY", raising=False)

    config = Settings(api_key="test_api_key")

    assert config.api_key == "test_api_key"
    assert config.base_url == "https://translation-api.ghananlp.org"
    assert config.timeout == TIMEOUT
    assert config.retry_attempts == RETRY_ATTEMPTS
    assert "translation" in config.endpoints
    assert "asr" in config.endpoints
    assert "tts" in config.endpoints


def test_endpoints_include_base_url():
    config = Settings(api_key="key")
    assert config.endpoints["translation"].startswith(config.base_url)
    assert config.endpoints["asr"].startswith(config.base_url)
    assert config.endpoints["tts"].startswith(config.base_url)


def test_extra_fields_are_forbidden():
    with pytest.raises(ValidationError):
        Settings(api_key="key", unknown_field="oops")


def test_http_base_url_rejected():
    with pytest.raises(ValidationError, match="HTTPS"):
        Settings(api_key="key", base_url="http://translation-api.ghananlp.org")


def test_custom_timeout_and_retries():
    config = Settings(api_key="key", timeout=60, retry_attempts=5)
    assert config.timeout == 60
    assert config.retry_attempts == 5


def test_config_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("KHAYA_API_KEY", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text("KHAYA_API_KEY=test_api_key\n")

    monkeypatch.setenv("KHAYA_API_KEY", "test_api_key")

    config = DevSettings(_env_file=str(env_file))
    assert config.api_key == "test_api_key"
