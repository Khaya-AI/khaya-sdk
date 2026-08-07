# Text-to-Speech (TTS)

Convert text to spoken audio using `synthesize()` or `asynthesize()`.

## Basic usage

```python
from khaya import KhayaClient

with KhayaClient(api_key) as khaya:
    result = khaya.synthesize("Maakye", "twi")
    result.save("output.wav")
```

Or access the raw bytes directly via `result.audio`:

```python
with KhayaClient(api_key) as khaya:
    result = khaya.synthesize("Maakye", "twi")
    with open("output.wav", "wb") as f:
        f.write(result.audio)
```

`synthesize()` returns a `SynthesisResult` with:

| Attribute | Type | Description |
|-----------|------|-------------|
| `audio` | `bytes` | Raw audio bytes |
| `save(path)` | method | Write audio to a file |

!!! note
    Most codes are shared with ASR, but not all: Konkomba (Likpakpaanl) is
    `"xon_likpakpaanl"` for ASR and `"xon"` for TTS.

## Supported languages

32 languages — see the [language reference](../languages.md#tts-languages).
TTS codes differ from ASR codes for some languages.

## Speaker voices

All languages share the same multilingual speaker pool. Pass a `speaker` to control the voice:

| Speaker | Description |
|---------|-------------|
| `"male_low"` | Male, lower pitch |
| `"male_high"` | Male, higher pitch |
| `"female"` | Female |

```python
with KhayaClient(api_key) as khaya:
    result = khaya.synthesize("Maakye", "twi", speaker="female")
    result.save("output.wav")
```

The `speaker` argument is optional — the API uses a default voice when omitted.

An unrecognised speaker is rejected before the request is sent:

```python
khaya.synthesize("Maakye", "twi", speaker="robot")
# TTSGenerationError: Unknown speaker 'robot'. Supported speakers: female, male_high, male_low
```

The API accepts any string here and silently uses its default voice, so a
typo would otherwise go unnoticed. `khaya.constants.SUPPORTED_TTS_SPEAKERS`
holds the accepted values.

## Playing audio directly

Use any audio library to play back without saving to disk:

```python
# with sounddevice + soundfile
import io
import soundfile as sf
import sounddevice as sd

with KhayaClient(api_key) as khaya:
    result = khaya.synthesize("Maakye", "twi")
    data, samplerate = sf.read(io.BytesIO(result.audio))
    sd.play(data, samplerate)
    sd.wait()
```

## Synthesizing longer text

The API has a per-request character limit. For longer content, split into sentences:

Each call returns a complete WAV file. Concatenating the bytes does **not**
work — the first header declares only the first chunk's length. Decode the
parts and write a single stream:

```python
import io
import re

import numpy as np
import soundfile as sf

def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]

with KhayaClient(api_key) as khaya:
    parts = [khaya.synthesize(chunk, "twi").audio for chunk in split_sentences(long_text)]

frames = []
samplerate = None
for part in parts:
    data, samplerate = sf.read(io.BytesIO(part))
    frames.append(data)

sf.write("output.wav", np.concatenate(frames), samplerate)
```

`soundfile` is not an SDK dependency: `pip install soundfile`.

## Error handling

```python
from khaya.exceptions import TTSGenerationError, AuthenticationError, APIError

try:
    result = khaya.synthesize("Maakye", "twi")
except TTSGenerationError as e:
    # Raised when text or language is empty
    print(f"TTS error: {e.message}")
except AuthenticationError:
    print("Check your API key.")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

See [Error Handling](error-handling.md) for the full exception reference.
