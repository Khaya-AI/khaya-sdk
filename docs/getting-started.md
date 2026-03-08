# Getting Started

## Installation

=== "pip"

    ```bash
    pip install khaya
    ```

=== "uv"

    ```bash
    uv add khaya
    ```

Requires Python 3.11 or later.

## Get an API key

Sign up at [https://translation.ghananlp.org](https://translation.ghananlp.org) to get your API key.

## Authentication

Pass your key directly to the client, or set the `KHAYA_API_KEY` environment variable and pass it from there:

```bash
export KHAYA_API_KEY=your_api_key_here
```

```python
import os
from khaya import KhayaClient

client = KhayaClient(os.environ["KHAYA_API_KEY"])
```

## Your first requests

### Translate text

```python
import os
from khaya import KhayaClient

with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    result = khaya.translate("Good morning", "en-tw")
    print(result.json())  # "Maakye"
```

### Transcribe audio

```python
with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    result = khaya.transcribe("recording.wav", "tw")
    print(result.json())
```

### Synthesize speech

```python
with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    result = khaya.synthesize("Maakye", "tw")
    with open("output.wav", "wb") as f:
        f.write(result.content)
```

## Using the context manager

The `with` statement ensures HTTP connections are closed properly. It is the recommended usage pattern:

```python
with KhayaClient(api_key) as khaya:
    ...
```

If you manage the lifecycle yourself, call `khaya.http_client.close()` when you are done.

## Next steps

- [Translation guide](guides/translation.md) — all language pairs and tips
- [ASR guide](guides/asr.md) — audio format requirements
- [TTS guide](guides/tts.md) — saving and playing audio
- [Error handling](guides/error-handling.md) — catch the right exception
- [Async usage](guides/async.md) — `async with` and `await`
