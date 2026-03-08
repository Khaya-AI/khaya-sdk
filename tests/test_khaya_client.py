"""Unit tests for KhayaClient.

All HTTP calls are mocked via the respx_mock fixture. No live API or API key
is required. Integration tests live in test_integration.py.
"""

import asyncio
import warnings

import httpx
import pytest

from khaya import KhayaClient
from khaya.config import Settings
from khaya.exceptions import (
    APIError,
    ASRTranscriptionError,
    AuthenticationError,
    RateLimitError,
    TranslationError,
    TTSGenerationError,
)
from khaya.models import SynthesisResult, TranscriptionResult, TranslationResult

BASE_URL = "https://translation.ghananlp.org"
TRANSLATE_URL = f"{BASE_URL}/v1/translate"
TTS_URL = f"{BASE_URL}/tts/v1/tts"
ASR_URL = f"{BASE_URL}/asr/v1/transcribe"


def make_client(api_key: str = "test-api-key", retry_attempts: int = 1) -> KhayaClient:
    """Return a KhayaClient configured for unit testing (no retries by default)."""
    config = Settings(api_key=api_key, retry_attempts=retry_attempts)
    return KhayaClient(api_key=api_key, config=config)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


class TestTranslate:
    def test_success(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json="Ɛte sɛn?")
        )
        result = make_client().translate("Hello", "en-tw")
        assert isinstance(result, TranslationResult)
        assert result.text == "Ɛte sɛn?"
        assert result.source_language == "en"
        assert result.target_language == "tw"

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
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(401, text="Access Denied")
        )
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


# ---------------------------------------------------------------------------
# ASR
# ---------------------------------------------------------------------------


class TestTranscribe:
    def test_success(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(
            return_value=httpx.Response(200, json="me ho ye")
        )
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
        respx_mock.post(ASR_URL).mock(
            return_value=httpx.Response(401, text="Access Denied")
        )
        with pytest.raises(AuthenticationError):
            make_client().transcribe(str(audio), "tw")

    def test_500_raises_api_error(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(
            return_value=httpx.Response(500, text="Server Error")
        )
        with pytest.raises(APIError):
            make_client().transcribe(str(audio), "tw")

    def test_language_sent_as_query_param(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        route = respx_mock.post(ASR_URL).mock(
            return_value=httpx.Response(200, json="me ho ye")
        )
        make_client().transcribe(str(audio), "tw")
        assert route.calls[0].request.url.params["language"] == "tw"


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------


class TestSynthesize:
    def test_success(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=b"\xff\xfb audio bytes")
        )
        result = make_client().synthesize("Hello", "tw")
        assert isinstance(result, SynthesisResult)
        assert isinstance(result.audio, bytes)
        assert result.language == "tw"

    def test_save_writes_file(self, respx_mock, tmp_path):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=b"\xff\xfb audio bytes")
        )
        result = make_client().synthesize("Hello", "tw")
        out = tmp_path / "output.wav"
        result.save(str(out))
        assert out.read_bytes() == b"\xff\xfb audio bytes"

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
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(401, text="Access Denied")
        )
        with pytest.raises(AuthenticationError):
            make_client().synthesize("Hello", "tw")

    def test_429_raises_rate_limit_error(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(429, text="Too Many Requests")
        )
        with pytest.raises(RateLimitError):
            make_client().synthesize("Hello", "tw")

    def test_500_raises_api_error(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(500, text="Server Error")
        )
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
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json="Ɛte sɛn?")
        )
        with KhayaClient("test-api-key") as client:
            result = client.translate("Hello", "en-tw")
        assert result.text == "Ɛte sɛn?"

    async def test_async_context_manager(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json="Ɛte sɛn?")
        )
        async with KhayaClient("test-api-key") as client:
            result = await client.atranslate("Hello", "en-tw")
        assert result.text == "Ɛte sɛn?"


# ---------------------------------------------------------------------------
# Async API
# ---------------------------------------------------------------------------


class TestAsync:
    async def test_atranslate_success(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json="Ɛte sɛn?")
        )
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
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(401, text="Access Denied")
        )
        with pytest.raises(AuthenticationError):
            await make_client().atranslate("Hello", "en-tw")

    async def test_atranscribe_success(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(
            return_value=httpx.Response(200, json="me ho ye")
        )
        result = await make_client().atranscribe(str(audio), "tw")
        assert isinstance(result, TranscriptionResult)
        assert result.text == "me ho ye"

    async def test_atranscribe_file_not_found_raises(self):
        with pytest.raises(ASRTranscriptionError):
            await make_client().atranscribe("nonexistent/audio.wav", "tw")

    async def test_asynthesize_success(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=b"\xff\xfb audio bytes")
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
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(401, text="Access Denied")
        )
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

    async def test_async_transport_error_retries_then_raises(
        self, respx_mock, monkeypatch
    ):
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
        assert api.sync_client.is_closed

    async def test_async_context_manager_closes_client(self):
        from khaya.config import Settings
        from khaya.services.base_api import BaseApi

        config = Settings(api_key="test-key")
        api = BaseApi(config)
        async with api as ctx:
            assert ctx is api
        assert api.async_client.is_closed


# ---------------------------------------------------------------------------
# Language validation warnings
# ---------------------------------------------------------------------------


class TestLanguageValidationWarnings:
    def test_unknown_language_pair_warns(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json="...")
        )
        with pytest.warns(UserWarning, match="xx-yy"):
            make_client().translate("Hello", "xx-yy")

    def test_known_language_pair_no_warning(self, respx_mock):
        respx_mock.post(TRANSLATE_URL).mock(
            return_value=httpx.Response(200, json="Ɛte sɛn?")
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            make_client().translate("Hello", "en-tw")

    def test_unknown_asr_language_warns(self, respx_mock, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
        respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json="text"))
        with pytest.warns(UserWarning, match="xx"):
            make_client().transcribe(str(audio), "xx")

    def test_unknown_tts_language_warns(self, respx_mock):
        respx_mock.post(TTS_URL).mock(
            return_value=httpx.Response(200, content=b"audio")
        )
        with pytest.warns(UserWarning, match="xx"):
            make_client().synthesize("Hello", "xx")
