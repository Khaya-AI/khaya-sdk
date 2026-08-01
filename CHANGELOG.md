# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added

- `APIError.code`, `APIError.details`, and `APIError.activity_id` — the API's structured error envelope is now parsed instead of discarded. `activity_id` is the server-side correlation ID to quote in support requests.
- Non-JSON success bodies (e.g. an HTML page from the gateway on a 200) now raise `APIError` instead of leaking a raw `json.JSONDecodeError`.
- HTML error pages are summarised by their `<title>` rather than embedding kilobytes of markup in the exception message.

### Changed

- **Removed client-side language validation.** The SDK no longer emits a `UserWarning` for language codes absent from its constants. The API accepts multiple spellings per language (`en-tw`, `en-twi` and `eng-twi` all work) and gains languages independently of SDK releases, so the check produced false warnings on valid calls. `SUPPORTED_*` constants remain as reference data. Unsupported codes are reported by the API as an `APIError` with `code="VALIDATION_FAILED"`.
- `Retry-After` delays are capped at 60s (`MAX_RETRY_AFTER_SECONDS`). Previously a server sending `Retry-After: 86400` would block the caller for 24 hours per attempt.
- HTTP clients are created lazily. A purely synchronous caller no longer allocates — and leak — an unused `AsyncClient`, and vice versa; `aclose()` now closes both.
- `Settings.retry_attempts` must be `>= 1` and `Settings.timeout` must be `> 0`. `retry_attempts=0` previously skipped the request entirely and then raised "Request failed after retries".

### Fixed

- `KhayaClient` docstring no longer claims the API key can be supplied via the `KHAYA_API_KEY` environment variable — the constructor requires it explicitly.
- Corrected provenance comments in `constants.py`: the cited `/asr/v1/languages` and `/tts/v1/languages` endpoints return 404 and 403 respectively, so those lists are unverified.

- Typed result objects: `TranslationResult`, `TranscriptionResult`, `SynthesisResult` — methods no longer return raw `httpx.Response`.
- `SynthesisResult.save(path)` helper for writing audio bytes to a file.
- `TranslationResult.source_language` and `TranslationResult.target_language` attributes.
- Structured logging across all modules using `logging.getLogger(__name__)`:
  - `khaya.services.base_api` — HTTP attempt number, retryable status codes, backoff duration, transport errors, successful response status.
  - `khaya.services.translation` — character count and language pair per request.
  - `khaya.services.asr` — language and audio file size per request.
  - `khaya.services.tts` — character count, language, and output audio size per request.
- `NullHandler` on the `khaya` logger in `__init__.py` — SDK is silent by default.
- MkDocs Material documentation site with guides, API reference, and architecture diagrams.

### Changed

- `translate()`, `atranslate()` now return `TranslationResult` instead of `httpx.Response`.
- `transcribe()`, `atranscribe()` now return `TranscriptionResult` instead of `httpx.Response`.
- `synthesize()`, `asynthesize()` now return `SynthesisResult` instead of `httpx.Response`.
- API base URL default kept as `https://translation-api.ghananlp.org`.

### Removed

- `logger.py` — logging setup moved to `__init__.py`.
- `ABC` base class from `BaseApi` (no abstract methods existed).

---

## [0.1.0] — 2026-03-08

### Added

- `KhayaClient` with synchronous and asynchronous API for translation, ASR, and TTS.
- `translate(text, language_pair)` — text translation across African language pairs.
- `transcribe(audio_file_path, language)` — speech-to-text from `.wav` audio.
- `synthesize(text, language)` — text-to-speech returning raw audio bytes.
- Async counterparts: `atranslate`, `atranscribe`, `asynthesize`.
- Sync and async context manager support (`with`/`async with`).
- Structured exception hierarchy: `APIError`, `AuthenticationError`,
  `RateLimitError`, `TranslationError`, `TTSGenerationError`, `ASRTranscriptionError`.
- Exponential backoff retry logic with jitter for transient failures (429, 5xx).
- `Retry-After` header support for rate-limit responses.
- Pydantic-based `Settings` with HTTPS enforcement and strict field validation.
- `SUPPORTED_LANGUAGE_PAIRS`, `SUPPORTED_ASR_LANGUAGES`, `SUPPORTED_TTS_LANGUAGES` constants.
- MIT license.
