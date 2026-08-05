"""Integration tests — require a real KHAYA_API_KEY and network access.

Run with:
    pytest -m integration

Deselected in the normal CI run; executed on a schedule by
.github/workflows/smoke.yml so that backend outages and response-shape
changes are noticed without waiting for a user to report them.

These assert the SDK's public contract against the live API. They are
deliberately loose about *content* (translations and transcriptions are model
outputs and will drift) and strict about *shape* — the types, attributes, and
exceptions the SDK promises.
"""

import os
from pathlib import Path

import pytest

from khaya import KhayaClient
from khaya.exceptions import APIError, AuthenticationError
from khaya.models import SynthesisResult, TranscriptionResult, TranslationResult

AUDIO_FIXTURE = Path(__file__).parent / "me_ho_ye.wav"


@pytest.fixture(scope="session")
def integration_client():
    api_key = os.environ.get("KHAYA_API_KEY")
    if not api_key:
        pytest.skip("KHAYA_API_KEY environment variable not set")
    with KhayaClient(api_key) as client:
        yield client


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_translate_en_to_tw(integration_client):
    result = integration_client.translate("Good morning", "en-tw")
    assert isinstance(result, TranslationResult)
    assert isinstance(result.text, str) and result.text.strip()
    assert result.source_language == "en"
    assert result.target_language == "tw"


@pytest.mark.integration
@pytest.mark.parametrize("pair", ["en-tw", "en-twi", "eng-twi"])
def test_api_accepts_multiple_code_spellings(integration_client, pair):
    """The SDK must not second-guess codes the API accepts.

    This is the check that justifies removing client-side language
    validation; if the API ever narrows what it accepts, this fails and the
    decision gets revisited.
    """
    result = integration_client.translate("Good morning", pair)
    assert result.text.strip()


@pytest.mark.integration
def test_unsupported_pair_returns_structured_error(integration_client):
    with pytest.raises(APIError) as exc:
        integration_client.translate("Hello", "en-zz")
    assert exc.value.status_code == 400
    assert exc.value.code == "VALIDATION_FAILED"
    assert any(d.get("target") == "language_pair" for d in exc.value.details)


@pytest.mark.integration
def test_invalid_key_raises_authentication_error():
    with KhayaClient("0" * 32) as client:
        with pytest.raises(AuthenticationError) as exc:
            client.translate("Hello", "en-tw")
    assert exc.value.status_code == 401


# ---------------------------------------------------------------------------
# ASR
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_transcribe_twi(integration_client):
    result = integration_client.transcribe(str(AUDIO_FIXTURE), "tw")
    assert isinstance(result, TranscriptionResult)
    assert isinstance(result.text, str) and result.text.strip()
    assert result.language == "tw"


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_synthesize_twi(integration_client):
    result = integration_client.synthesize("Me ho yɛ", "twi")
    assert isinstance(result, SynthesisResult)
    assert isinstance(result.audio, bytes)
    assert len(result.audio) > 0
    assert result.language == "twi"


@pytest.mark.integration
def test_synthesized_audio_can_be_saved(integration_client, tmp_path):
    result = integration_client.synthesize("Me ho yɛ", "twi")
    out = tmp_path / "output.wav"
    result.save(str(out))
    assert out.stat().st_size == len(result.audio) > 0


# ---------------------------------------------------------------------------
# Async surface
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_async_translate(integration_client):
    result = await integration_client.atranslate("Good morning", "en-tw")
    assert isinstance(result, TranslationResult)
    assert result.text.strip()
