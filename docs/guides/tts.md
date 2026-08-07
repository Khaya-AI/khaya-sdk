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
    TTS language codes differ from ASR codes for the same language.
    For example, Asante Twi is `"tw"` in ASR but `"twi"` in TTS.

## Supported languages

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

Unlike language codes, an unrecognised speaker is rejected by the SDK before
the request is sent:

```python
khaya.synthesize("Maakye", "twi", speaker="robot")
# TTSGenerationError: Unknown speaker 'robot'. Supported speakers: female, male_high, male_low
```

The API accepts any string here and silently falls back to its default
voice, so a typo would otherwise produce the wrong voice with no error.
`khaya.constants.SUPPORTED_TTS_SPEAKERS` holds the accepted values.

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

Each call returns a complete WAV file, header and all. Concatenating the bytes
does **not** work: `b"".join(parts)` produces a file whose first header
declares only the first chunk's length, so every decoder plays chunk one and
ignores the rest. Decode the parts and write a single stream instead:

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

`soundfile` is not a dependency of the SDK — install it with
`pip install soundfile` (it brings `numpy`).

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
