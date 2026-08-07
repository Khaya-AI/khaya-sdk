from typing import get_args

import pytest
from pydantic import ValidationError

from khaya.config import (
    API_ENDPOINTS,
    AsrVersion,
    DevSettings,
    Settings,
    TranslationVersion,
    TtsVersion,
)
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


def test_zero_retry_attempts_rejected():
    # retry_attempts=0 used to skip the request entirely and then raise
    # "Request failed after retries" — describing retries that never ran.
    with pytest.raises(ValidationError):
        Settings(api_key="key", retry_attempts=0)


def test_non_positive_timeout_rejected():
    with pytest.raises(ValidationError):
        Settings(api_key="key", timeout=0)


def test_config_from_env_file(tmp_path, monkeypatch):
    monkeypatch.delenv("KHAYA_API_KEY", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text("KHAYA_API_KEY=from_env_file\n")

    # Deliberately no monkeypatch.setenv here: with the variable also exported,
    # the assertion passes whether or not _env_file is ever read.
    config = DevSettings(_env_file=str(env_file))
    assert config.api_key == "from_env_file"


# ---------------------------------------------------------------------------
# Endpoint registry
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("service", "versions"),
    [
        ("translation", TranslationVersion),
        ("asr", AsrVersion),
        ("tts", TtsVersion),
    ],
)
def test_every_selectable_version_has_a_path(service, versions):
    """The failure mode: widen the Literal, forget the registry entry."""
    for version in get_args(versions):
        assert (service, version) in API_ENDPOINTS, f"{service} {version} has no path"


def test_registry_has_no_paths_that_cannot_be_selected():
    selectable = (
        {("translation", v) for v in get_args(TranslationVersion)}
        | {("asr", v) for v in get_args(AsrVersion)}
        | {("tts", v) for v in get_args(TtsVersion)}
    )
    assert set(API_ENDPOINTS) == selectable


def test_defaults_resolve_to_the_measured_best_versions():
    endpoints = Settings(api_key="k").endpoints
    assert endpoints["translation"].endswith("/v1/translate")
    assert endpoints["asr"].endswith("/asr/v3/transcribe")
    assert endpoints["tts"].endswith("/tts/v1/tts")


def test_tts_v2_uses_its_renamed_route():
    """v2 is not /tts/v2/tts — that 404s. The registry must encode the rename."""
    endpoints = Settings(api_key="k", tts_version="v2").endpoints
    assert endpoints["tts"].endswith("/tts/v2/synthesize")


@pytest.mark.parametrize(
    ("field", "value"),
    [("translation_version", "v3"), ("asr_version", "v4"), ("tts_version", "v3")],
)
def test_unavailable_versions_are_rejected_at_construction(field, value):
    with pytest.raises(ValidationError):
        Settings(api_key="k", **{field: value})
