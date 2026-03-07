"""Integration tests — require a real KHAYA_API_KEY and network access.

Run with:
    pytest -m integration

Skipped by default in CI.
"""

import os

import pytest

from khaya import KhayaClient


@pytest.fixture(scope="session")
def integration_client():
    api_key = os.environ.get("KHAYA_API_KEY")
    if not api_key:
        pytest.skip("KHAYA_API_KEY environment variable not set")
    return KhayaClient(api_key)


@pytest.mark.integration
def test_translate_en_to_tw(integration_client):
    result = integration_client.translate("Hello", "en-tw")
    assert result.status_code == 200
    assert result.text


@pytest.mark.integration
def test_transcribe_twi(integration_client):
    audio_path = "tests/me_ho_ye.wav"
    result = integration_client.transcribe(audio_path, "tw")
    assert result.status_code == 200
    assert result.json() == "me ho yɛ"


@pytest.mark.integration
def test_synthesize_twi(integration_client):
    result = integration_client.synthesize("Me ho yɛ", "tw")
    assert result.status_code == 200
    assert isinstance(result.content, bytes)
    assert len(result.content) > 0
