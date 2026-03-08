# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
- API base URL corrected to `https://translation.ghananlp.org`.

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
