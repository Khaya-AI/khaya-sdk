# Khaya SDK

[![PyPI version](https://badge.fury.io/py/khaya.svg)](https://pypi.org/project/khaya/)
[![CI](https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Khaya-AI/khaya-sdk/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-khaya--sdk.readthedocs.io-blue)](https://khaya-sdk.readthedocs.io)

Python SDK for the [Khaya AI](https://khaya.ai) Khaya API — providing translation, automatic speech recognition (ASR), and text-to-speech (TTS) for African languages.

## Installation

```bash
pip install khaya
```

## Authentication

Get an API key at [https://translation.ghananlp.org](https://translation.ghananlp.org) and set it as an environment variable:

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
    print(result.text)

    # Transcribe a Twi audio file
    result = khaya.transcribe("path/to/audio.wav", "tw")
    print(result.text)

    # Synthesize speech in Twi
    result = khaya.synthesize("Me ho yɛ", "twi")
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

        result = await khaya.atranscribe("path/to/audio.wav", "tw")
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

## Supported Languages

### Translation pairs

| Code | Language |
|------|----------|
| `en` | English |
| `tw` | Twi |
| `ee` | Ewe |
| `gaa` | Ga |
| `fat` | Fante |
| `yo` | Yoruba |
| `dag` | Dagbani |
| `ki` | Kikuyu |
| `gur` | Gurene |
| `luo` | Luo |
| `mer` | Kimeru |
| `kus` | Kusaal |

Language pair format: `"<source>-<target>"`, e.g. `"en-tw"` or `"tw-en"`. All pairs are bidirectional with English as the pivot language.

### ASR languages

| Code | Language |
|------|----------|
| `eng` | African English |
| `fra` | African French |
| `atw` | Akuapem Twi |
| `bwu` | Buli |
| `dga` | Dagaare |
| `dag` | Dagbani |
| `ada` | Dangme |
| `ewe` | Ewe |
| `fat` | Fante |
| `gaa` | Ga |
| `gjn` | Gonja |
| `gur` | Gurene |
| `hau` | Hausa |
| `ibo` | Igbo |
| `xsm` | Kasem |
| `kik` | Kikuyu |
| `kin` | Kinyarwanda |
| `xon_likoonli` | Konkomba-Likoonli |
| `xon_likpakpaanl` | Konkomba-Likpakpaanl |
| `kri` | Krio |
| `kus` | Kusaal |
| `luo` | Luo |
| `maw` | Mampruli |
| `men` | Mende |
| `mer` | Meru |
| `pcm` | Naija Pidgin |
| `nzi` | Nzema |
| `sna` | Shona |
| `swa` | Swahili |
| `tem` | Temne |
| `twi` | Twi |
| `wlx` | Wali |
| `wol` | Wolof |
| `yor` | Yoruba |
### TTS languages

| Code | Language |
|------|----------|
| `atw` | Akuapem Twi |
| `twi` | Asante Twi |
| `dga` | Dagaare |
| `dag` | Dagbani |
| `ada` | Dangme |
| `eng` | English |
| `ewe` | Ewe |
| `fat` | Fante |
| `fra` | French |
| `gaa` | Ga |
| `gjn` | Gonja |
| `gur` | Gurene |
| `hau` | Hausa |
| `ibo` | Igbo |
| `xsm` | Kasem |
| `kik` | Kikuyu |
| `lxn` | Konkomba (Likoonli) |
| `xon` | Konkomba (Likpakpaanl) |
| `kri` | Krio |
| `kus` | Kusaal |
| `luo` | Luo |
| `maw` | Mampruli |
| `men` | Mende |
| `mer` | Meru/Kimeru |
| `nzi` | Nzema |
| `pcm` | Pidgin |
| `sna` | Shona |
| `swa` | Swahili |
| `tem` | Temne |
| `wlx` | Wali |
| `wol` | Wolof |
| `yor` | Yoruba |
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
