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

BASE_URL = "https://translation-api.ghananlp.org"
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
        respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="Ɛte sɛn?"))
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


# ---------------------------------------------------------------------------
# ASR
# ---------------------------------------------------------------------------


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
        respx_mock.post(TTS_URL).mock(return_value=httpx.Response(200, content=b"audio"))
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            make_client().synthesize("Hello", "xx")
