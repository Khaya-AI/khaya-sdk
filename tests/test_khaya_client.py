"""Unit tests for KhayaClient.

All HTTP calls are mocked via the respx_mock fixture. No live API or API key
is required. Integration tests live in test_integration.py.
"""

import asyncio
import json
import warnings

import httpx
import pytest

from khaya import KhayaClient
from khaya.config import Settings
from khaya.exceptions import (
    APIError,
    ASRTranscriptionError,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    TranslationError,
    TTSGenerationError,
)
from khaya.models import SynthesisResult, TranscriptionResult, TranslationResult

BASE_URL = "https://api.khaya.ai"
TRANSLATE_URL = f"{BASE_URL}/translate/v1/translate"
TTS_URL = f"{BASE_URL}/tts/v1/synthesize"
ASR_URL = f"{BASE_URL}/asr/v1/transcribe"

# TTS responses must look like audio or the content-type guard rejects them.
WAV_BYTES = b"RIFF$\x00\x00\x00WAVEfmt " + b"\x00" * 24
AUDIO_HEADERS = {"content-type": "audio/wav"}


def make_client(api_key: str = "test-api-key", retry_attempts: int = 1) -> KhayaClient:
    """Return a KhayaClient configured for unit testing (no retries by default)."""
    config = Settings(api_key=api_key, retry_attempts=retry_attempts)
    return KhayaClient(api_key=api_key, config=config)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


class TestTranslate:
    def test_success(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="Ɛte sɛn?"))
        result = make_client().translate("Hello", "en-tw")
        assert isinstance(result, TranslationResult)
        assert result.text == "Ɛte sɛn?"
        assert result.source_language == "en"
        assert result.target_language == "tw"

    def test_whitespace_only_text_rejected(self):
        with pytest.raises(TranslationError):
            make_client().translate("   ", "eng-twi")

    def test_empty_text_raises_translation_error(self):
        with pytest.raises(TranslationError):
            make_client().translate("", "en-tw")

    def test_empty_pair_raises_translation_error(self):
        with pytest.raises(TranslationError):
            make_client().translate("Hello", "")

    def test_missing_api_key_raises_authentication_error(self):
        with pytest.raises(AuthenticationError):
            make_client(api_key="").translate("Hello", "en-tw")

    def test_401_raises_authentication_error(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(401, text="Access Denied"))
        with pytest.raises(AuthenticationError):
            make_client().translate("Hello", "en-tw")

    def test_429_raises_rate_limit_error(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(429, text="Too Many Requests")
        )
        with pytest.raises(RateLimitError):
            make_client().translate("Hello", "en-tw")

    def test_500_raises_api_error(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        with pytest.raises(APIError):
            make_client().translate("Hello", "en-tw")

    def test_platform_object_response_is_parsed(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(
                200,
                json={"text": "Maakye", "source_language": "eng", "target_language": "twi"},
            )
        )
        result = make_client().translate("Good morning", "eng-twi")
        assert result.text == "Maakye"
        assert (result.source_language, result.target_language) == ("eng", "twi")

    def test_unrecognised_response_shape_raises(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json={"out": 1}))
        with pytest.raises(TranslationError, match="Unexpected translation response"):
            make_client().translate("Hello", "en-tw")

    async def test_async_platform_object_response_is_parsed(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json={"text": "Maakye"})
        )
        assert (await make_client().atranslate("Good morning", "eng-twi")).text == "Maakye"

    def test_request_body_uses_the_in_lang_format(self, respx_mock):
        route = respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="x"))
        make_client().translate("Hello", "eng-twi")
        assert json.loads(route.calls.last.request.content) == {"in": "Hello", "lang": "eng-twi"}


# ---------------------------------------------------------------------------
# ASR
# ---------------------------------------------------------------------------


class TestRequestHeaders:
    """The platform authenticates with a Bearer token and 415s a wrong upload type."""

    def test_api_key_is_sent_as_a_bearer_token(self, respx_mock):
        route = respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json="Me ho yɛ")
        )
        make_client(api_key="secret-key").translate("How are you", "en-tw")
        headers = route.calls.last.request.headers
        assert headers["authorization"] == "Bearer secret-key"
        assert "ocp-apim-subscription-key" not in headers

    def test_no_authorization_header_without_a_key(self, respx_mock):
        """Unkeyed calls (the public catalogues) must not send an empty Bearer token."""
        route = respx_mock.get(f"{BASE_URL}/tts/v1/languages").mock(
            return_value=httpx.Response(200, json={"languages": {}})
        )
        make_client(api_key="").http_client.request("GET", f"{BASE_URL}/tts/v1/languages")
        assert "authorization" not in route.calls.last.request.headers

    def test_explicit_none_headers_are_tolerated(self, respx_mock):
        route = respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="x"))
        make_client().http_client.request("POST", TRANSLATE_URL, json={}, headers=None)
        assert route.calls.last.request.headers["authorization"] == "Bearer test-api-key"

    async def test_async_explicit_none_headers_are_tolerated(self, respx_mock):
        route = respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="x"))
        await make_client().http_client.arequest("POST", TRANSLATE_URL, json={}, headers=None)
        assert route.calls.last.request.headers["authorization"] == "Bearer test-api-key"

    def test_json_requests_still_declare_json(self, respx_mock):
        route = respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json="Me ho yɛ")
        )
        make_client().translate("How are you", "en-tw")
        assert route.calls.last.request.headers["content-type"] == "application/json"

    @pytest.mark.parametrize(
        ("filename", "expected"),
        [
            ("clip.wav", "audio/"),
            ("clip.mp3", "audio/"),
            ("clip.mp4", "video/"),
            ("clip.unknownext", "application/octet-stream"),
            ("clip.txt", "application/octet-stream"),
            ("clip", "application/octet-stream"),
        ],
    )
    def test_asr_upload_declares_a_type_the_gateway_accepts(
        self, respx_mock, tmp_path, filename, expected
    ):
        audio = tmp_path / filename
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        route = respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json="me ho ye"))
        make_client().transcribe(str(audio), "twi")
        request = route.calls.last.request
        assert request.headers["content-type"].startswith(expected)
        assert request.headers["authorization"] == "Bearer test-api-key"

    async def test_async_asr_upload_declares_a_type_the_gateway_accepts(self, respx_mock, tmp_path):
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        route = respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json="me ho ye"))
        await make_client().atranscribe(str(audio), "twi")
        assert route.calls.last.request.headers["content-type"].startswith("audio/")


class TestTranscribe:
    def test_success(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json="me ho ye"))
        result = make_client().transcribe(str(audio), "tw")
        assert isinstance(result, TranscriptionResult)
        assert result.text == "me ho ye"
        assert result.language == "tw"

    def test_file_not_found_raises_asr_error(self):
        with pytest.raises(ASRTranscriptionError):
            make_client().transcribe("nonexistent/path/audio.wav", "tw")

    def test_missing_api_key_raises_authentication_error(self):
        with pytest.raises(AuthenticationError):
            make_client(api_key="").transcribe("any.wav", "tw")

    def test_401_raises_authentication_error(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(return_value=httpx.Response(401, text="Access Denied"))
        with pytest.raises(AuthenticationError):
            make_client().transcribe(str(audio), "tw")

    def test_500_raises_api_error(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(return_value=httpx.Response(500, text="Server Error"))
        with pytest.raises(APIError):
            make_client().transcribe(str(audio), "tw")

    def test_v3_structured_body_populates_text(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json={"text": "Me ho yɛ."}))
        result = make_client().transcribe(str(audio), "twi")
        assert result.text == "Me ho yɛ."
        assert result.warnings == []
        assert result.timings is None

    def test_api_warnings_are_surfaced(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(
            return_value=httpx.Response(
                200,
                json={"text": "Me ho yɛ.", "warnings": ["'tw' is a legacy code."]},
            )
        )
        result = make_client().transcribe(str(audio), "tw")
        assert result.warnings == ["'tw' is a legacy code."]

    def test_v1_bare_string_still_parses(self, respx_mock, tmp_path):
        """A bare JSON string body is still accepted, carrying no envelope."""
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json="Me ho yɛ."))
        result = make_client().transcribe(str(audio), "twi")
        assert result.text == "Me ho yɛ."
        assert result.warnings == []

    def test_word_timings_are_parsed(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        route = respx_mock.post(ASR_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "text": "Me ho",
                    "timings": {
                        "unit": "seconds",
                        "granularity": "word",
                        "segments": [],
                        "words": [
                            {"word": "Me", "start": 0.0, "end": 0.12},
                            {"word": "ho", "start": 0.12, "end": 0.30},
                        ],
                    },
                },
            )
        )
        result = make_client().transcribe(str(audio), "twi", timestamps="word")
        assert route.calls.last.request.url.params["timestamps"] == "word"
        assert result.timings is not None
        assert result.timings.granularity == "word"
        assert [w.word for w in result.timings.words] == ["Me", "ho"]
        assert result.timings.words[0].end == 0.12

    def test_segment_timings_are_parsed(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "text": "Me ho yɛ.",
                    "timings": {
                        "unit": "seconds",
                        "granularity": "segment",
                        "words": [],
                        "segments": [{"text": "Me ho yɛ.", "start": 0.0, "end": 1.0}],
                    },
                },
            )
        )
        result = make_client().transcribe(str(audio), "twi", timestamps="segment")
        assert result.timings.segments[0].text == "Me ho yɛ."
        assert result.timings.segments[0].end == 1.0

    def test_timestamps_omitted_from_params_when_unset(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        route = respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json={"text": "hi"}))
        make_client().transcribe(str(audio), "twi")
        assert "timestamps" not in route.calls.last.request.url.params

    def test_invalid_timestamps_rejected_before_request(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        route = respx_mock.post(ASR_URL)
        with pytest.raises(ASRTranscriptionError, match="word.*segment"):
            make_client().transcribe(str(audio), "twi", timestamps="true")
        assert route.call_count == 0

    def test_language_sent_as_query_param(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        route = respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json="me ho ye"))
        make_client().transcribe(str(audio), "tw")
        assert route.calls[0].request.url.params["language"] == "tw"


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------


class TestSynthesize:
    def test_success(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=WAV_BYTES, headers=AUDIO_HEADERS)
        )
        result = make_client().synthesize("Hello", "tw")
        assert isinstance(result, SynthesisResult)
        assert isinstance(result.audio, bytes)
        assert result.language == "tw"

    def test_save_writes_file(self, respx_mock, tmp_path):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=WAV_BYTES, headers=AUDIO_HEADERS)
        )
        result = make_client().synthesize("Hello", "tw")
        out = tmp_path / "output.wav"
        result.save(str(out))
        assert out.read_bytes() == WAV_BYTES

    def test_speaker_is_sent_as_speaker_id(self, respx_mock):
        route = respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=WAV_BYTES, headers=AUDIO_HEADERS)
        )
        make_client().synthesize("Hello", "twi", speaker="female")
        assert json.loads(route.calls.last.request.content)["speaker_id"] == "female"

    def test_speaker_omitted_from_payload_when_none(self, respx_mock):
        route = respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=WAV_BYTES, headers=AUDIO_HEADERS)
        )
        make_client().synthesize("Hello", "twi")
        assert "speaker_id" not in json.loads(route.calls.last.request.content)

    @pytest.mark.parametrize("speaker", ["male_low", "male_high", "female"])
    def test_every_supported_speaker_is_accepted(self, respx_mock, speaker):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=WAV_BYTES, headers=AUDIO_HEADERS)
        )
        assert make_client().synthesize("Hello", "twi", speaker=speaker).audio == WAV_BYTES

    def test_unknown_speaker_raises_before_any_request(self, respx_mock):
        route = respx_mock.post(TTS_URL)
        with pytest.raises(TTSGenerationError, match="Unknown speaker"):
            make_client().synthesize("Hello", "twi", speaker="robot")
        # Must not burn a request.
        assert route.call_count == 0

    def test_non_audio_200_raises_rather_than_returning_html(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(
                200,
                content=b"<html><head><title>503 Service Unavailable</title></head></html>",
                headers={"content-type": "text/html"},
            )
        )
        with pytest.raises(TTSGenerationError, match="Expected audio"):
            make_client().synthesize("Hello", "twi")

    def test_audio_without_content_type_is_accepted_on_riff_magic(self, respx_mock):
        respx_mock.post(TTS_URL).mock(return_value=httpx.Response(200, content=WAV_BYTES))
        assert make_client().synthesize("Hello", "twi").audio == WAV_BYTES

    def test_whitespace_only_text_rejected(self):
        """The API bills whitespace and returns invented speech."""
        with pytest.raises(TTSGenerationError):
            make_client().synthesize("   \n\t ", "twi")

    def test_save_names_the_missing_directory(self, respx_mock, tmp_path):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=WAV_BYTES, headers=AUDIO_HEADERS)
        )
        result = make_client().synthesize("Me ho yɛ", "twi")
        missing = tmp_path / "nope" / "out.wav"
        with pytest.raises(TTSGenerationError, match="no such directory"):
            result.save(str(missing))

    def test_empty_text_raises_tts_error(self):
        with pytest.raises(TTSGenerationError):
            make_client().synthesize("", "tw")

    def test_empty_language_raises_tts_error(self):
        with pytest.raises(TTSGenerationError):
            make_client().synthesize("Hello", "")

    def test_missing_api_key_raises_authentication_error(self):
        with pytest.raises(AuthenticationError):
            make_client(api_key="").synthesize("Hello", "tw")

    def test_401_raises_authentication_error(self, respx_mock):
        respx_mock.post(TTS_URL).mock(return_value=httpx.Response(401, text="Access Denied"))
        with pytest.raises(AuthenticationError):
            make_client().synthesize("Hello", "tw")

    def test_429_raises_rate_limit_error(self, respx_mock):
        respx_mock.post(TTS_URL).mock(return_value=httpx.Response(429, text="Too Many Requests"))
        with pytest.raises(RateLimitError):
            make_client().synthesize("Hello", "tw")

    def test_500_raises_api_error(self, respx_mock):
        respx_mock.post(TTS_URL).mock(return_value=httpx.Response(500, text="Server Error"))
        with pytest.raises(APIError):
            make_client().synthesize("Hello", "tw")


# ---------------------------------------------------------------------------
# Retry logic
# ---------------------------------------------------------------------------


class TestRetry:
    def test_retries_configured_times_on_500(self, respx_mock, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        config = Settings(api_key="test-api-key", retry_attempts=3)
        client = KhayaClient(api_key="test-api-key", config=config)

        route = respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(500, text="Server Error")
        )
        with pytest.raises(APIError):
            client.translate("Hello", "en-tw")

        assert route.call_count == 3

    def test_no_retry_on_401(self, respx_mock, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        config = Settings(api_key="test-api-key", retry_attempts=3)
        client = KhayaClient(api_key="test-api-key", config=config)

        route = respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(401, text="Access Denied")
        )
        with pytest.raises(AuthenticationError):
            client.translate("Hello", "en-tw")

        assert route.call_count == 1

    def test_succeeds_after_transient_failure(self, respx_mock, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        config = Settings(api_key="test-api-key", retry_attempts=3)
        client = KhayaClient(api_key="test-api-key", config=config)

        respx_mock.post(TRANSLATE_URL).mock(
            side_effect=[
                httpx.Response(500, text="Error"),
                httpx.Response(500, text="Error"),
                httpx.Response(200, json="Ɛte sɛn?"),
            ]
        )
        result = client.translate("Hello", "en-tw")
        assert result.text == "Ɛte sɛn?"

    def test_retry_after_header_respected(self, respx_mock, monkeypatch):
        sleep_calls = []
        monkeypatch.setattr("time.sleep", lambda d: sleep_calls.append(d))
        config = Settings(api_key="test-api-key", retry_attempts=2)
        client = KhayaClient(api_key="test-api-key", config=config)

        respx_mock.post(TRANSLATE_URL).mock(
            side_effect=[
                httpx.Response(429, text="Rate limited", headers={"Retry-After": "5"}),
                httpx.Response(200, json="Ɛte sɛn?"),
            ]
        )
        result = client.translate("Hello", "en-tw")
        assert result.text == "Ɛte sɛn?"
        assert 5.0 in sleep_calls


# ---------------------------------------------------------------------------
# Context managers
# ---------------------------------------------------------------------------


class TestContextManager:
    def test_sync_context_manager(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="Ɛte sɛn?"))
        with KhayaClient("test-api-key") as client:
            result = client.translate("Hello", "en-tw")
        assert result.text == "Ɛte sɛn?"

    async def test_async_context_manager(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="Ɛte sɛn?"))
        async with KhayaClient("test-api-key") as client:
            result = await client.atranslate("Hello", "en-tw")
        assert result.text == "Ɛte sɛn?"


# ---------------------------------------------------------------------------
# Async API
# ---------------------------------------------------------------------------


class TestAsync:
    async def test_atranslate_success(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="Ɛte sɛn?"))
        result = await make_client().atranslate("Hello", "en-tw")
        assert isinstance(result, TranslationResult)
        assert result.text == "Ɛte sɛn?"

    async def test_atranslate_empty_text_raises(self):
        with pytest.raises(TranslationError):
            await make_client().atranslate("", "en-tw")

    async def test_atranslate_missing_api_key_raises(self):
        with pytest.raises(AuthenticationError):
            await make_client(api_key="").atranslate("Hello", "en-tw")

    async def test_atranslate_401_raises_authentication_error(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(401, text="Access Denied"))
        with pytest.raises(AuthenticationError):
            await make_client().atranslate("Hello", "en-tw")

    async def test_atranscribe_success(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json="me ho ye"))
        result = await make_client().atranscribe(str(audio), "tw")
        assert isinstance(result, TranscriptionResult)
        assert result.text == "me ho ye"

    async def test_atranscribe_file_not_found_raises(self):
        with pytest.raises(ASRTranscriptionError):
            await make_client().atranscribe("nonexistent/audio.wav", "tw")

    async def test_asynthesize_success(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=WAV_BYTES, headers=AUDIO_HEADERS)
        )
        result = await make_client().asynthesize("Hello", "tw")
        assert isinstance(result, SynthesisResult)
        assert isinstance(result.audio, bytes)

    async def test_asynthesize_empty_text_raises(self):
        with pytest.raises(TTSGenerationError):
            await make_client().asynthesize("", "tw")

    async def test_asynthesize_missing_api_key_raises(self):
        with pytest.raises(AuthenticationError):
            await make_client(api_key="").asynthesize("Hello", "tw")

    async def test_asynthesize_401_raises_authentication_error(self, respx_mock):
        respx_mock.post(TTS_URL).mock(return_value=httpx.Response(401, text="Access Denied"))
        with pytest.raises(AuthenticationError):
            await make_client().asynthesize("Hello", "tw")

    async def test_async_retry_on_500(self, respx_mock, monkeypatch):
        sleep_calls = []

        async def fake_sleep(d):
            sleep_calls.append(d)

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        config = Settings(api_key="test-api-key", retry_attempts=2)
        client = KhayaClient(api_key="test-api-key", config=config)

        respx_mock.post(TRANSLATE_URL).mock(
            side_effect=[
                httpx.Response(500, text="Error"),
                httpx.Response(200, json="Ɛte sɛn?"),
            ]
        )
        result = await client.atranslate("Hello", "en-tw")
        assert result.text == "Ɛte sɛn?"
        assert len(sleep_calls) == 1


# ---------------------------------------------------------------------------
# Transport error retry
# ---------------------------------------------------------------------------


class TestTransportErrorRetry:
    def test_sync_transport_error_retries_then_raises(self, respx_mock, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        config = Settings(api_key="test-api-key", retry_attempts=2)
        client = KhayaClient(api_key="test-api-key", config=config)

        respx_mock.post(TRANSLATE_URL).mock(side_effect=httpx.ConnectError("refused"))
        with pytest.raises(APIError, match="Transport error"):
            client.translate("Hello", "en-tw")

    def test_sync_transport_error_succeeds_on_retry(self, respx_mock, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        config = Settings(api_key="test-api-key", retry_attempts=2)
        client = KhayaClient(api_key="test-api-key", config=config)

        respx_mock.post(TRANSLATE_URL).mock(
            side_effect=[
                httpx.ConnectError("refused"),
                httpx.Response(200, json="Ɛte sɛn?"),
            ]
        )
        result = client.translate("Hello", "en-tw")
        assert result.text == "Ɛte sɛn?"

    async def test_async_transport_error_retries_then_raises(self, respx_mock, monkeypatch):
        async def noop_sleep(_):
            pass

        monkeypatch.setattr(asyncio, "sleep", noop_sleep)
        config = Settings(api_key="test-api-key", retry_attempts=2)
        client = KhayaClient(api_key="test-api-key", config=config)

        respx_mock.post(TRANSLATE_URL).mock(side_effect=httpx.ConnectError("refused"))
        with pytest.raises(APIError, match="Transport error"):
            await client.atranslate("Hello", "en-tw")


# ---------------------------------------------------------------------------
# BaseApi context manager
# ---------------------------------------------------------------------------


class TestBaseApiContextManager:
    def test_sync_context_manager_closes_client(self):
        from khaya.config import Settings
        from khaya.services.base_api import BaseApi

        config = Settings(api_key="test-key")
        api = BaseApi(config)
        with api as ctx:
            assert ctx is api
            client = ctx.sync_client  # force creation
        assert client.is_closed

    async def test_async_context_manager_closes_client(self):
        from khaya.config import Settings
        from khaya.services.base_api import BaseApi

        config = Settings(api_key="test-key")
        api = BaseApi(config)
        async with api as ctx:
            assert ctx is api
            client = ctx.async_client  # force creation
        assert client.is_closed


# ---------------------------------------------------------------------------
# Client lifecycle — clients are created lazily so an unused one never leaks
# ---------------------------------------------------------------------------


class TestClientLifecycle:
    def test_clients_are_created_lazily(self):
        api = make_client().http_client
        assert api._sync_client is None
        assert api._async_client is None

    def test_sync_use_never_allocates_an_async_client(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="Ɛte sɛn?"))
        with KhayaClient("test-api-key") as client:
            client.translate("Hello", "en-tw")
        api = client.http_client
        assert api._sync_client is not None and api._sync_client.is_closed
        assert api._async_client is None  # never created, so nothing leaked

    async def test_async_close_also_closes_the_sync_client(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="Ɛte sɛn?"))
        client = make_client()
        client.translate("Hello", "en-tw")  # creates the sync client
        await client.atranslate("Hello", "en-tw")  # creates the async client
        await client.http_client.aclose()
        assert client.http_client._sync_client.is_closed
        assert client.http_client._async_client.is_closed


# ---------------------------------------------------------------------------
# Structured error envelopes
# ---------------------------------------------------------------------------


class TestErrorEnvelope:
    def test_validation_envelope_is_parsed(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(
                400,
                json={
                    "error": {
                        "code": "VALIDATION_FAILED",
                        "message": "The request payload contains invalid parameters.",
                        "details": [
                            {
                                "code": "UNSUPPORTED_LANGUAGE_PAIR",
                                "message": "Language combination en-zz cannot be used",
                                "target": "language_pair",
                            }
                        ],
                    }
                },
            )
        )
        with pytest.raises(APIError) as exc:
            make_client().translate("Hello", "en-zz")

        err = exc.value
        assert err.code == "VALIDATION_FAILED"
        assert err.message == "The request payload contains invalid parameters."
        assert err.details[0]["target"] == "language_pair"
        assert "en-zz cannot be used" in str(err)

    def test_activity_id_is_surfaced(self, respx_mock, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(
                500,
                json={
                    "statusCode": 500,
                    "message": "Internal server error",
                    "activityId": "41d51993-e979-4d99-a8fd-eea93a3d0267",
                },
            )
        )
        with pytest.raises(APIError) as exc:
            make_client().translate("Hello", "en-tw")

        assert exc.value.activity_id == "41d51993-e979-4d99-a8fd-eea93a3d0267"
        assert exc.value.message == "Internal server error"
        assert "41d51993" in str(exc.value)

    def test_statuscode_envelope_on_401(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(
                401,
                json={
                    "statusCode": 401,
                    "message": "Access denied due to invalid subscription key.",
                },
            )
        )
        with pytest.raises(AuthenticationError) as exc:
            make_client().translate("Hello", "en-tw")
        assert exc.value.message == "Access denied due to invalid subscription key."

    def test_html_error_body_is_truncated(self, respx_mock):
        html = "<!DOCTYPE html><html><head><title>Web App - Unavailable</title>" + (
            "<style>" + "x" * 4000 + "</style>"
        )
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(403, text=html, headers={"content-type": "text/html"})
        )
        with pytest.raises(APIError) as exc:
            make_client().synthesize("Hello", "twi")

        assert exc.value.status_code == 403
        assert len(exc.value.message) < 300  # not the whole 4KB document
        # The page title is the signal; the inline CSS is not.
        assert "Web App - Unavailable" in exc.value.message
        assert "x" * 100 not in exc.value.message

    def test_untitled_non_json_body_falls_back_to_snippet(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(
                502, text="upstream connect error", headers={"content-type": "text/plain"}
            )
        )
        with pytest.raises(APIError) as exc:
            make_client(retry_attempts=1).synthesize("Hello", "twi")
        assert "upstream connect error" in exc.value.message


# ---------------------------------------------------------------------------
# Non-JSON success bodies must not escape the SDK exception hierarchy
# ---------------------------------------------------------------------------


class TestNonJsonSuccessBody:
    def test_html_200_raises_api_error(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(
                200, text="<html>gateway</html>", headers={"content-type": "text/html"}
            )
        )
        with pytest.raises(APIError, match="Expected a JSON response"):
            make_client().translate("Hello", "en-tw")

    def test_empty_200_raises_api_error(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, content=b""))
        with pytest.raises(APIError):
            make_client().transcribe(str(audio), "tw")

    async def test_async_html_200_raises_api_error(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(
                200, text="<html>gateway</html>", headers={"content-type": "text/html"}
            )
        )
        with pytest.raises(APIError, match="Expected a JSON response"):
            await make_client().atranslate("Hello", "en-tw")


# ---------------------------------------------------------------------------
# Retry-After is capped
# ---------------------------------------------------------------------------


class TestRetryAfterCap:
    def test_excessive_retry_after_is_capped(self, respx_mock, monkeypatch):
        from khaya.services.base_api import MAX_RETRY_AFTER_SECONDS

        sleeps = []
        monkeypatch.setattr("time.sleep", lambda d: sleeps.append(d))
        respx_mock.post(TRANSLATE_URL).mock(
            side_effect=[
                httpx.Response(429, text="slow down", headers={"Retry-After": "86400"}),
                httpx.Response(200, json="Ɛte sɛn?"),
            ]
        )
        config = Settings(api_key="test-api-key", retry_attempts=2)
        result = KhayaClient("test-api-key", config=config).translate("Hi", "en-tw")

        assert result.text == "Ɛte sɛn?"
        assert sleeps == [MAX_RETRY_AFTER_SECONDS]

    def test_http_date_retry_after_falls_back_to_backoff(self, respx_mock, monkeypatch):
        sleeps = []
        monkeypatch.setattr("time.sleep", lambda d: sleeps.append(d))
        respx_mock.post(TRANSLATE_URL).mock(
            side_effect=[
                httpx.Response(
                    503,
                    text="unavailable",
                    headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"},
                ),
                httpx.Response(200, json="Ɛte sɛn?"),
            ]
        )
        config = Settings(api_key="test-api-key", retry_attempts=2)
        result = KhayaClient("test-api-key", config=config).translate("Hi", "en-tw")

        assert result.text == "Ɛte sɛn?"
        assert len(sleeps) == 1 and 1.0 <= sleeps[0] <= 2.0  # exponential, not a date

    async def test_async_retry_after_is_capped(self, respx_mock, monkeypatch):
        from khaya.services.base_api import MAX_RETRY_AFTER_SECONDS

        sleeps = []

        async def fake_sleep(d):
            sleeps.append(d)

        monkeypatch.setattr("asyncio.sleep", fake_sleep)
        respx_mock.post(TRANSLATE_URL).mock(
            side_effect=[
                httpx.Response(429, text="slow down", headers={"Retry-After": "86400"}),
                httpx.Response(200, json="Ɛte sɛn?"),
            ]
        )
        config = Settings(api_key="test-api-key", retry_attempts=2)
        result = await KhayaClient("test-api-key", config=config).atranslate("Hi", "en-tw")

        assert result.text == "Ɛte sɛn?"
        assert sleeps == [MAX_RETRY_AFTER_SECONDS]


# ---------------------------------------------------------------------------
# Language codes the API accepts must not be second-guessed by the SDK
# ---------------------------------------------------------------------------


class TestNoClientSideLanguageValidation:
    @pytest.mark.parametrize("pair", ["en-tw", "en-twi", "eng-twi", "xx-yy"])
    def test_no_warning_for_any_language_pair(self, respx_mock, pair):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json="Mema wo akwaaba")
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            result = make_client().translate("Good morning", pair)
        assert result.text == "Mema wo akwaaba"

    def test_no_warning_for_unlisted_asr_language(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json="text"))
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            make_client().transcribe(str(audio), "xx")

    def test_no_warning_for_unlisted_tts_language(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=WAV_BYTES, headers=AUDIO_HEADERS)
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            make_client().synthesize("Hello", "xx")


# ---------------------------------------------------------------------------
# Platform gateway error envelope: {"detail": {"error": ..., ...}}
# ---------------------------------------------------------------------------


class TestPlatformErrorEnvelope:
    def test_invalid_key(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(
                401,
                json={
                    "detail": {
                        "error": "INVALID_API_KEY",
                        "message": "API key not found or revoked",
                    }
                },
            )
        )
        with pytest.raises(AuthenticationError) as exc:
            make_client().translate("Hello", "en-tw")
        assert exc.value.code == "INVALID_API_KEY"
        assert exc.value.message == "API key not found or revoked"

    def test_code_stands_in_for_a_missing_message(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(401, json={"detail": {"error": "EMPTY_API_KEY"}})
        )
        with pytest.raises(AuthenticationError) as exc:
            make_client().translate("Hello", "en-tw")
        assert exc.value.message == "EMPTY_API_KEY"

    def test_validation_details_and_request_id(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(
                422,
                json={
                    "detail": {
                        "error": "VALIDATION_FAILED",
                        "message": "The request payload contains invalid parameters.",
                        "details": [
                            {
                                "code": "MISSING_LANGUAGE",
                                "message": "No language selected",
                                "target": "language",
                            }
                        ],
                        "request_id": "req-123",
                    }
                },
            )
        )
        with pytest.raises(APIError) as exc:
            make_client().synthesize("Hello", "twi")
        err = exc.value
        assert err.status_code == 422
        assert err.code == "VALIDATION_FAILED"
        assert err.details[0]["target"] == "language"
        assert err.activity_id == "req-123"
        assert "language: No language selected" in str(err)

    def test_insufficient_credits(self, respx_mock):
        route = respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(
                402,
                json={
                    "detail": {
                        "error": "INSUFFICIENT_CREDITS",
                        "balance": 3,
                        "estimated_cost": 10,
                        "top_up_url": "https://khaya.ai/billing",
                    }
                },
            )
        )
        with pytest.raises(InsufficientCreditsError) as exc:
            make_client(retry_attempts=3).translate("Hello", "en-tw")
        assert exc.value.code == "INSUFFICIENT_CREDITS"
        assert "balance 3" in exc.value.message
        assert "~10" in exc.value.message
        assert "https://khaya.ai/billing" in exc.value.message
        assert route.call_count == 1  # topping up is the only fix; retrying is not

    def test_insufficient_credits_is_an_api_error(self):
        assert issubclass(InsufficientCreditsError, APIError)

    def test_rate_limit(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(
                429,
                json={
                    "detail": {
                        "error": "RATE_LIMIT_EXCEEDED",
                        "violated_limit": "rate_limit_per_minute",
                        "retry_after_seconds": 12,
                    }
                },
                headers={"Retry-After": "12"},
            )
        )
        with pytest.raises(RateLimitError) as exc:
            make_client().translate("Hello", "en-tw")
        assert exc.value.code == "RATE_LIMIT_EXCEEDED"
        assert exc.value.message == "Rate limit exceeded: rate_limit_per_minute (Retry-After: 12s)"
        assert "Retry-After: 12s" in exc.value.message

    @pytest.mark.parametrize("code", ["ROUTE_NOT_ALLOWED", "SIGNUP_REQUIRED"])
    def test_forbidden(self, respx_mock, code):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(403, json={"detail": {"error": code, "message": "no"}})
        )
        with pytest.raises(APIError) as exc:
            make_client().translate("Hello", "en-tw")
        assert (exc.value.status_code, exc.value.code) == (403, code)

    def test_unsupported_media_type(self, respx_mock, tmp_path):
        audio = tmp_path / "clip.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(
            return_value=httpx.Response(
                415,
                json={
                    "detail": {
                        "error": "UNSUPPORTED_MEDIA_TYPE",
                        "message": "Content-Type must be audio/*, video/*, or application/octet-stream",
                    }
                },
            )
        )
        with pytest.raises(APIError) as exc:
            make_client().transcribe(str(audio), "twi")
        assert exc.value.code == "UNSUPPORTED_MEDIA_TYPE"

    def test_string_detail(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(404, json={"detail": "Not Found"})
        )
        with pytest.raises(APIError) as exc:
            make_client().translate("Hello", "en-tw")
        assert (exc.value.status_code, exc.value.message) == (404, "Not Found")

    def test_upstream_502_is_retried(self, respx_mock, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)
        route = respx_mock.post(TRANSLATE_URL).mock(
            side_effect=[
                httpx.Response(
                    502, json={"detail": {"error": "UPSTREAM_ERROR", "request_id": "r1"}}
                ),
                httpx.Response(200, json="Maakye"),
            ]
        )
        assert make_client(retry_attempts=2).translate("Hello", "en-tw").text == "Maakye"
        assert route.call_count == 2
