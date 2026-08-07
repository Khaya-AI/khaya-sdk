<p align="center">
  <img src="https://raw.githubusercontent.com/Khaya-AI/khaya-sdk/main/docs/assets/khaya-logo.png" alt="Khaya AI" width="110">
</p>

<h1 align="center">Khaya SDK</h1>

<p align="center">
  Translation, speech recognition, and text-to-speech for African languages.
</p>

<p align="center">
  <a href="https://pypi.org/project/khaya/"><img src="https://img.shields.io/pypi/v/khaya" alt="PyPI"></a>
  <a href="https://pypi.org/project/khaya/"><img src="https://img.shields.io/pypi/pyversions/khaya" alt="Python versions"></a>
  <a href="https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml"><img src="https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://khaya-sdk.readthedocs.io"><img src="https://img.shields.io/badge/docs-readthedocs-blue" alt="Docs"></a>
  <a href="LICENSE"><img src="https://img.shields.io/pypi/l/khaya" alt="License"></a>
</p>

Python SDK for the [Khaya AI](https://khaya.ai) API — translation, automatic
speech recognition (ASR), and text-to-speech (TTS) across 30+ African
languages, with sync and async clients, typed results, and automatic retries.

**[Documentation](https://khaya-sdk.readthedocs.io)** · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md)

## Installation

```bash
pip install khaya
```

## Authentication

Get an API key at [https://translation.ghananlp.org](https://translation.ghananlp.org) and set it as an environment variable:

```bash
export KHAYA_API_KEY=your_api_key_here
```

`Settings` also reads `KHAYA_BASE_URL`, `KHAYA_TIMEOUT`, and
`KHAYA_RETRY_ATTEMPTS`.

## Quick Start

```python
import os
from khaya import KhayaClient

with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    # Translate text from English to Twi
    result = khaya.translate("Hello, how are you?", "en-tw")
    print(result.text)

    # Transcribe a Twi audio file
    result = khaya.transcribe("path/to/audio.wav", "twi")
    print(result.text)

    # Synthesize speech in Twi, optionally choosing a voice
    result = khaya.synthesize("Me ho yɛ", "twi", speaker="female")
    result.save("output.wav")
```

Each method returns a typed result object rather than a raw HTTP response:
`TranslationResult` and `TranscriptionResult` expose `.text`, and
`SynthesisResult` exposes `.audio` bytes plus a `.save(path)` helper.

## Async Usage

```python
import asyncio
import os
from khaya import KhayaClient

async def main():
    async with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
        result = await khaya.atranslate("Hello", "en-tw")
        print(result.text)

        result = await khaya.atranscribe("path/to/audio.wav", "twi")
        print(result.text)

        result = await khaya.asynthesize("Me ho yɛ", "twi")
        result.save("output.wav")

asyncio.run(main())
```

## Error Handling

All errors raise exceptions — never return error dicts. Catch the appropriate exception:

```python
from khaya import KhayaClient
from khaya.exceptions import (
    AuthenticationError,
    RateLimitError,
    TranslationError,
    APIError,
)

khaya = KhayaClient(api_key="your-key")

try:
    result = khaya.translate("Hello", "en-tw")
    print(result.text)
except AuthenticationError:
    print("Invalid API key. Check your KHAYA_API_KEY.")
except RateLimitError as e:
    print(f"Rate limit hit: {e.message}")
except TranslationError as e:
    print(f"Translation failed ({e.status_code}): {e.message}")
except APIError as e:
    print(f"API error ({e.status_code}): {e.message}")
```

## Supported languages

| Service | Languages |
|---------|-----------|
| Translation | 12, paired with English (22 pairs) |
| Speech recognition | 34 |
| Text-to-speech | 32, with 3 speaker voices |

Full tables, and the difference between legacy and ISO 639-3 codes, are in the
**[language reference](https://khaya-sdk.readthedocs.io/en/latest/languages/)**.

The SDK does not validate language codes — it sends what you pass and lets the
API decide, so you can use any code the API supports without waiting for an SDK
release.

## Configuration

```python
from khaya import KhayaClient
from khaya.config import Settings

config = Settings(
    api_key="your-key",
    timeout=60,          # seconds (default: 30)
    retry_attempts=5,    # retries on transient failures (default: 3)
)
khaya = KhayaClient(api_key="your-key", config=config)
```

## Development

```bash
# Install all dependency groups
uv sync --extra test --extra dev

# Run unit tests (no API key required)
uv run pytest -m "not integration"

# Run with coverage
uv run pytest -m "not integration" --cov=src/khaya --cov-report=term-missing

# Lint and type-check
uv run ruff check src/khaya
uv run mypy src/khaya

# Install pre-commit hooks
uv run pre-commit install
```

## License

[MIT](LICENSE)
