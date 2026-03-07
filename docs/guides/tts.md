# Text-to-Speech (TTS)

Convert text to spoken audio using `synthesize()` or `asynthesize()`.

## Basic usage

```python
from khaya import KhayaClient

with KhayaClient(api_key) as khaya:
    result = khaya.synthesize("Maakye", "tw")
    with open("output.wav", "wb") as f:
        f.write(result.content)
```

The audio is returned as raw bytes in `result.content`.

## Supported languages

| Code | Language |
|------|----------|
| `tw` | Twi |
| `gaa` | Ga |
| `dag` | Dagbani |
| `ee` | Ewe |
| `yo` | Yoruba |

## Playing audio directly

Use any audio library to play back without saving to disk:

```python
# with sounddevice + soundfile
import io
import soundfile as sf
import sounddevice as sd

with KhayaClient(api_key) as khaya:
    result = khaya.synthesize("Maakye", "tw")
    data, samplerate = sf.read(io.BytesIO(result.content))
    sd.play(data, samplerate)
    sd.wait()
```

## Synthesizing longer text

The API has a per-request character limit. For longer content, split into sentences:

```python
import re

def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

with KhayaClient(api_key) as khaya:
    chunks = split_sentences(long_text)
    audio_parts = [khaya.synthesize(chunk, "tw").content for chunk in chunks]

combined = b"".join(audio_parts)
with open("output.wav", "wb") as f:
    f.write(combined)
```

## Error handling

```python
from khaya.exceptions import TTSGenerationError, AuthenticationError, APIError

try:
    result = khaya.synthesize("Maakye", "tw")
except TTSGenerationError as e:
    # Raised when text or language is empty
    print(f"TTS error: {e.message}")
except AuthenticationError:
    print("Check your API key.")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

See [Error Handling](error-handling.md) for the full exception reference.
