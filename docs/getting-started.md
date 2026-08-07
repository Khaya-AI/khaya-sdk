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

`KhayaClient` takes the key as its first argument:

```python
from khaya import KhayaClient

client = KhayaClient("your_api_key_here")
```

Most people keep it in the environment and pass it from there:

```bash
export KHAYA_API_KEY=your_api_key_here
```

```python
import os
from khaya import KhayaClient

client = KhayaClient(os.environ["KHAYA_API_KEY"])
```

`Settings` reads `KHAYA_`-prefixed variables on its own — `KHAYA_API_KEY`,
`KHAYA_BASE_URL`, `KHAYA_TIMEOUT`, `KHAYA_RETRY_ATTEMPTS` — which is useful for
tuning timeouts and retries without touching code. See
[Configuration](guides/configuration.md).

## Your first requests

### Translate text

```python
import os
from khaya import KhayaClient

with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    result = khaya.translate("Good morning", "en-tw")
    print(result.text)  # the Twi translation
```

### Transcribe audio

```python
with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    result = khaya.transcribe("recording.wav", "tw")
    print(result.text)
```

### Synthesize speech

```python
with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    result = khaya.synthesize("Maakye", "twi")
    result.save("output.wav")
```

Pass `speaker="female"`, `"male_low"` or `"male_high"` to choose a voice.

## Using the context manager

The `with` statement ensures HTTP connections are closed properly. It is the recommended usage pattern:

```python
with KhayaClient(api_key) as khaya:
    ...
```

If you manage the lifecycle yourself, call `khaya.http_client.close()`, or
`await khaya.http_client.aclose()` if you have used any `a*` method —
`aclose()` closes both clients, `close()` leaves an async client open.

## Next steps

- [Translation guide](guides/translation.md) — all language pairs and tips
- [ASR guide](guides/asr.md) — audio format requirements
- [TTS guide](guides/tts.md) — saving and playing audio
- [Error handling](guides/error-handling.md) — catch the right exception
- [Async usage](guides/async.md) — `async with` and `await`
- [Language reference](languages.md) — every code for all three services
