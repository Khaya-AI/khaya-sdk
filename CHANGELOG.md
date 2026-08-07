# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

---

## [0.2.0] — 2026-08-07

This release changes the return type of every API method and removes
client-side language validation. See **Changed** for the migration notes.

### Added

- Typed result objects: `TranslationResult`, `TranscriptionResult`, `SynthesisResult` — methods no longer return raw `httpx.Response`.
- `SynthesisResult.save(path)` helper for writing audio bytes to a file.
- `TranslationResult.source_language` and `TranslationResult.target_language` attributes.
- Speaker selection for TTS: `synthesize(text, language, speaker=...)` and `asynthesize(...)` accept `"male_low"`, `"male_high"`, or `"female"`. Omitted, the API picks its default. An unrecognised speaker raises `TTSGenerationError` before the request is sent — the API accepts any string here and silently substitutes its default voice, so a typo would otherwise be invisible. `SUPPORTED_TTS_SPEAKERS` lists the values, sourced from `/tts/v1/speakers`.
- `APIError.code`, `APIError.details`, and `APIError.activity_id` — the API's structured error envelope is now parsed instead of discarded. `activity_id` is the server-side correlation ID to quote in support requests.
- Translation pairs for Luo (`en-luo`/`luo-en`), Kimeru (`en-mer`/`mer-en`), and Kusaal (`en-kus`/`kus-en`).
- ASR support for Buli (`bwu`) and Kinyarwanda (`kin`), which the reference list had never carried.
- Integration tests that pin `SUPPORTED_ASR_LANGUAGES`, `SUPPORTED_TTS_LANGUAGES`, and `SUPPORTED_TTS_SPEAKERS` to the live `/asr/v3/languages`, `/tts/v2/languages`, and `/tts/v1/speakers` catalogues, so reference data that drifts fails the scheduled smoke run.
- Structured logging across all modules using `logging.getLogger(__name__)`:
  - `khaya.services.base_api` — HTTP attempt number, retryable status codes, backoff duration, transport errors, successful response status.
  - `khaya.services.translation` — character count and language pair per request.
  - `khaya.services.asr` — language and audio file size per request.
  - `khaya.services.tts` — character count, language, and output audio size per request.
- `SUPPORTED_LANGUAGE_PAIRS`, `SUPPORTED_ASR_LANGUAGES`, `SUPPORTED_TTS_LANGUAGES`, and `SUPPORTED_TTS_SPEAKERS` are exported from the top-level package; they previously had to be imported from `khaya.constants`.
- `NullHandler` on the `khaya` logger in `__init__.py` — SDK is silent by default.
- MkDocs Material documentation site with guides, API reference, and architecture diagrams.
- Scheduled live smoke tests (`.github/workflows/smoke.yml`) that exercise the real endpoints daily and open an issue when they break. Unit tests mock every HTTP call, so they stay green through a backend outage.

### Changed

- **Return types.** `translate()`/`atranslate()` return `TranslationResult`, `transcribe()`/`atranscribe()` return `TranscriptionResult`, and `synthesize()`/`asynthesize()` return `SynthesisResult`, all in place of `httpx.Response`. Callers reading `response.json()["type"]` should read `result.text`; callers reading `response.content` from TTS should read `result.audio`.
- **Removed client-side language validation.** The SDK no longer emits a `UserWarning` for language codes absent from its constants. The API accepts multiple spellings per language (`en-tw`, `en-twi` and `eng-twi` all work) and gains languages independently of SDK releases, so the check produced false warnings on valid calls. `SUPPORTED_*` constants remain as reference data. Unsupported codes are reported by the API as an `APIError` with `code="VALIDATION_FAILED"`.
- Default `base_url` is `https://translation-api.ghananlp.org` (was `https://translation.ghananlp.org`, which no longer serves the API).
- **Settings now read `KHAYA_`-prefixed environment variables** — `KHAYA_API_KEY`, `KHAYA_BASE_URL`, `KHAYA_TIMEOUT`, `KHAYA_RETRY_ATTEMPTS`. Previously only `api_key` was bound by name and the remaining fields matched *unprefixed* `BASE_URL`, `TIMEOUT` and `RETRY_ATTEMPTS`, so a `BASE_URL` set for an unrelated application silently redirected the API key and every request body to that host. `KhayaClient(api_key)` still requires the key explicitly.
- Non-JSON success bodies (e.g. an HTML page from the gateway on a 200) now raise `APIError` instead of leaking a raw `json.JSONDecodeError`.
- `synthesize()`/`asynthesize()` verify the response is audio before returning it, raising `TTSGenerationError` otherwise. The gateway serves HTML error pages with a `200`, and TTS never decodes JSON, so those bodies were previously returned as `SynthesisResult.audio` and written to disk by `save()` as a `.wav` containing HTML.
- HTML error pages are summarised by their `<title>` rather than embedding kilobytes of markup in the exception message.
- `Retry-After` delays are capped at 60s (`MAX_RETRY_AFTER_SECONDS`). Previously a server sending `Retry-After: 86400` would block the caller for 24 hours per attempt. The exponential backoff now shares that cap — uncapped, `retry_attempts=10` meant roughly 8.5 minutes of uninterruptible sleeping.
- HTTP clients are created lazily. A purely synchronous caller no longer allocates — and leaks — an unused `AsyncClient`, and vice versa; `aclose()` now closes both.
- `Settings.retry_attempts` must be `>= 1` and `Settings.timeout` must be `> 0`. `retry_attempts=0` previously skipped the request entirely and then raised "Request failed after retries".

### Fixed

- The ASR/TTS language `ada` is named **Dangme**, not "Adangme", in `constants.py` and in the README and guide language tables.
- `KhayaClient` docstring no longer claims the API key can be supplied via the `KHAYA_API_KEY` environment variable — the constructor requires it explicitly.
- **Nine ASR language codes were wrong and rejected by the API**: `en_gh`, `gon`, `kas`, `kon_k`, `kon_l`, `mam`, `pid`, `wal`, `wo`. They are misspellings, not missing languages — each has an ISO 639-3 equivalent the API accepts, now used instead: `eng`, `gjn`, `xsm`, `xon_likoonli`, `xon_likpakpaanl`, `maw`, `pcm`, `wlx`, `wol`. `SUPPORTED_TTS_LANGUAGES` was also missing `eng`.
- Corrected provenance comments in `constants.py`. `/asr/v3/languages` and `/tts/v2/languages` both serve live catalogues and the lists are now generated from them; only `/asr/v1/languages` 404s. The previous claim that `/tts/v1/languages` returns 403 was wrong — it returns 200.
- The integration suite asserted against the pre-0.2.0 `httpx.Response` contract and an obsolete base URL, so it failed against the live API regardless of API health. It now asserts the SDK's public shape.
- The TTS "synthesizing longer text" recipe concatenated WAV files with `b"".join(...)`. Every chunk carries its own RIFF header, so the result was unplayable. The guide now decodes and rewrites a single stream.
- `docs/getting-started.md` recommended `http_client.close()` for manual lifecycle management, which leaves an `AsyncClient` open. It now points at `aclose()`.
- Sphinx `:meth:`/`:class:` roles in docstrings rendered as literal text under mkdocstrings, which is configured for Google style.
- `smoke.yml` passed vacuously when `KHAYA_API_KEY` was unset — every test skipped and the job went green. It now fails.
- `release.yml` validated the version only on the tag path. A manual dispatch to PyPI checked nothing; it now requires the checked-out commit to carry the matching tag.
- `internals.md` claimed the service layer builds "the correct JSON body or multipart form". ASR posts raw bytes.
- `test_config_from_env_file` set the environment variable it was using the `.env` file to test, so it passed whether or not the file was read.

### Removed

- `warn_if_unknown()` from `khaya.utils` — the client-side validation helper it backed is gone.
- `logger.py` — logging setup moved to `__init__.py`.
- `ABC` base class from `BaseApi` (no abstract methods existed).

---

## [0.1.1] — 2026-03-12

### Fixed

- Packaging metadata only; no functional changes.

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
