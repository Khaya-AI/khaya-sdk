# Khaya SDK

Python SDK for the [GhanaNLP](https://ghananlp.org) Khaya API — providing translation, automatic speech recognition (ASR), and text-to-speech (TTS) for African languages.

## Installation

```bash
pip install khaya
```

## Quick Start

```python
from khaya import KhayaClient
import os

khaya = KhayaClient(api_key=os.environ["KHAYA_API_KEY"])

# Translate text from English to Twi
result = khaya.translate("Hello, how are you?", "en-tw")
print(result.json())

# Transcribe an audio file
result = khaya.transcribe("path/to/audio.wav", "tw")
print(result.json())

# Synthesize speech
result = khaya.synthesize("Me ho yɛ", "tw")
with open("output.mp3", "wb") as f:
    f.write(result.content)
```

## Authentication

Get an API key at [https://translation-api.ghananlp.org](https://translation-api.ghananlp.org) and set it as an environment variable:

```bash
export KHAYA_API_KEY=your_api_key_here
```

## Supported Languages

See the [GhanaNLP API documentation](https://translation-api.ghananlp.org) for supported language pairs.

## Development

```bash
# Install dependencies
poetry install --with test,dev

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/khaya
```

## License

MIT
