"""Integration tests — require a real KHAYA_API_KEY and network access.

Run with ``pytest -m integration``. Deselected in normal CI; run on a
schedule by .github/workflows/smoke.yml.

Loose about content (model output drifts), strict about shape — the types,
attributes, and exceptions the SDK promises.
"""

import os
from pathlib import Path

import pytest

from khaya import KhayaClient
from khaya.config import Settings
from khaya.constants import (
    SUPPORTED_ASR_LANGUAGES,
    SUPPORTED_TTS_LANGUAGES,
    SUPPORTED_TTS_SPEAKERS,
)
from khaya.exceptions import APIError, AuthenticationError, TTSGenerationError
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
    """Justifies removing client-side validation: fails if the API narrows."""
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


@pytest.mark.integration
def test_legacy_language_code_surfaces_an_api_warning(integration_client):
    """v3 advises when a legacy code is used; v1 could not carry the advisory."""
    result = integration_client.transcribe(str(AUDIO_FIXTURE), "tw")
    assert result.text.strip()
    assert any("legacy" in w.lower() for w in result.warnings)


@pytest.mark.integration
def test_iso_language_code_produces_no_warning(integration_client):
    result = integration_client.transcribe(str(AUDIO_FIXTURE), "twi")
    assert result.warnings == []


@pytest.mark.integration
@pytest.mark.parametrize("granularity", ["word", "segment"])
def test_timestamps_return_alignment_data(integration_client, granularity):
    result = integration_client.transcribe(str(AUDIO_FIXTURE), "twi", timestamps=granularity)
    assert result.timings is not None
    assert result.timings.granularity == granularity
    assert result.timings.unit == "seconds"
    entries = result.timings.words if granularity == "word" else result.timings.segments
    assert entries, f"no {granularity} timings returned"
    assert entries[0].start >= 0.0
    assert entries[-1].end > entries[0].start


@pytest.mark.integration
def test_no_timings_unless_requested(integration_client):
    assert integration_client.transcribe(str(AUDIO_FIXTURE), "twi").timings is None


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
    # A size assertion alone passes for a saved HTML error page.
    assert out.read_bytes()[:4] == b"RIFF"


@pytest.mark.integration
@pytest.mark.parametrize("speaker", sorted(SUPPORTED_TTS_SPEAKERS))
def test_every_documented_speaker_synthesizes(integration_client, speaker):
    result = integration_client.synthesize("Me ho yɛ", "twi", speaker=speaker)
    assert result.audio[:4] == b"RIFF"


@pytest.mark.integration
def test_unknown_speaker_is_rejected_client_side(integration_client):
    """The API accepts any speaker string; this asserts the SDK does not."""
    with pytest.raises(TTSGenerationError, match="Unknown speaker"):
        integration_client.synthesize("Me ho yɛ", "twi", speaker="robot")


# ---------------------------------------------------------------------------
# Endpoint registry — proves every selectable version is a real route, which
# unit tests cannot: a wrong path is a 404, not a type error.
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.parametrize("version", ["v1", "v2"])
def test_every_translation_version_works(version):
    config = Settings(api_key=os.environ["KHAYA_API_KEY"], translation_version=version)
    with KhayaClient(config.api_key, config=config) as client:
        assert client.translate("Good morning", "eng-twi").text.strip()


@pytest.mark.integration
@pytest.mark.parametrize("version", ["v1", "v2", "v3"])
def test_every_asr_version_works(version):
    config = Settings(api_key=os.environ["KHAYA_API_KEY"], asr_version=version)
    with KhayaClient(config.api_key, config=config) as client:
        assert client.transcribe(str(AUDIO_FIXTURE), "twi").text.strip()


@pytest.mark.integration
@pytest.mark.parametrize("version", ["v1", "v2"])
def test_every_tts_version_works(version):
    config = Settings(api_key=os.environ["KHAYA_API_KEY"], tts_version=version)
    with KhayaClient(config.api_key, config=config) as client:
        assert client.synthesize("Me ho yɛ", "twi").audio[:4] == b"RIFF"


# ---------------------------------------------------------------------------
# Reference data — pinned to the live catalogues so drift fails the smoke run.
# ---------------------------------------------------------------------------


def _catalogue(client, path):
    response = client.http_client.request("GET", f"{client.config.base_url}{path}")
    return response.json()["languages"]


@pytest.mark.integration
def test_asr_language_list_matches_the_live_catalogue(integration_client):
    live = {entry["code"] for entry in _catalogue(integration_client, "/asr/v3/languages")}
    assert SUPPORTED_ASR_LANGUAGES == live


@pytest.mark.integration
def test_tts_language_list_matches_the_live_catalogue(integration_client):
    live = set(_catalogue(integration_client, "/tts/v2/languages").values())
    assert SUPPORTED_TTS_LANGUAGES == live


@pytest.mark.integration
def test_speaker_list_matches_the_live_catalogue(integration_client):
    # {"speakers": {"Multilingual": [...]}} — grouped by voice family.
    response = integration_client.http_client.request(
        "GET", f"{integration_client.config.base_url}/tts/v1/speakers"
    )
    live = {s for group in response.json()["speakers"].values() for s in group}
    assert SUPPORTED_TTS_SPEAKERS == live


# ---------------------------------------------------------------------------
# Async surface
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_async_translate(integration_client):
    result = await integration_client.atranslate("Good morning", "en-tw")
    assert isinstance(result, TranslationResult)
    assert result.text.strip()
