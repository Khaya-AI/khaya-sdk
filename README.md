# Khaya SDK

[![PyPI version](https://badge.fury.io/py/khaya.svg)](https://pypi.org/project/khaya/)
[![CI](https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Python SDK for the [GhanaNLP](https://ghananlp.org) Khaya API — providing translation, automatic speech recognition (ASR), and text-to-speech (TTS) for African languages.

## Installation

```bash
pip install khaya
```

## Authentication

Get an API key at [https://translation-api.ghananlp.org](https://translation-api.ghananlp.org) and set it as an environment variable:

```bash
export KHAYA_API_KEY=your_api_key_here
```

## Quick Start

```python
import os
from khaya import KhayaClient

with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    # Translate text from English to Twi
    result = khaya.translate("Hello, how are you?", "en-tw")
    print(result.json())

    # Transcribe a Twi audio file
    result = khaya.transcribe("path/to/audio.wav", "tw")
    print(result.json())

    # Synthesize speech in Twi
    result = khaya.synthesize("Me ho yɛ", "tw")
    with open("output.mp3", "wb") as f:
        f.write(result.content)
```

## Async Usage

```python
import asyncio
import os
from khaya import KhayaClient

async def main():
    async with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
        result = await khaya.atranslate("Hello", "en-tw")
        print(result.json())

        result = await khaya.atranscribe("path/to/audio.wav", "tw")
        print(result.json())

        result = await khaya.asynthesize("Me ho yɛ", "tw")
        with open("output.mp3", "wb") as f:
            f.write(result.content)

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
    print(result.json())
except AuthenticationError:
    print("Invalid API key. Check your KHAYA_API_KEY.")
except RateLimitError as e:
    print(f"Rate limit hit: {e.message}")
except TranslationError as e:
    print(f"Translation failed ({e.status_code}): {e.message}")
except APIError as e:
    print(f"API error ({e.status_code}): {e.message}")
```

## Supported Languages

### Translation pairs

| Code | Language |
|------|----------|
| `en` | English |
| `tw` | Twi |
| `ee` | Ewe |
| `gaa` | Ga |
| `dag` | Dagbani |
| `dga` | Dagaare |
| `fat` | Fante |
| `gur` | Gurene |
| `nzi` | Nzema |
| `kpo` | Ghanaian Pidgin |
| `yo` | Yoruba |
| `ki` | Kikuyu |

Language pair format: `"<source>-<target>"`, e.g. `"en-tw"` or `"tw-en"`.

### ASR languages

`tw`, `gaa`, `dag`, `ee`, `dga`, `fat`, `gur`, `nzi`, `kpo`, `yo`

### TTS languages

`tw`, `gaa`, `dag`, `ee`, `yo`

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
