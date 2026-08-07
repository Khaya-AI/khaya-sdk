# Speech Recognition (ASR)

Transcribe spoken audio to text using `transcribe()` or `atranscribe()`.

## Basic usage

```python
from khaya import KhayaClient

with KhayaClient(api_key) as khaya:
    result = khaya.transcribe("recording.wav", "twi")
    print(result.text)  # "me ho yɛ"
```

The second argument is the **language code** of the spoken language in the audio.

`transcribe()` returns a `TranscriptionResult` with:

| Attribute | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The transcribed string |
| `language` | `str` | Language code of the audio (e.g. `"twi"`) |

## Warnings from the API

The API flags deprecated language codes. Those advisories arrive on
`result.warnings` and are also logged at `WARNING`:

```python
result = khaya.transcribe("recording.wav", "tw")
print(result.warnings)
# ["Language code 'tw' is a legacy code. Please update to 'twi' (ISO 639-3)..."]
```

An empty list means the API had nothing to say. Prefer the ISO 639-3 codes and
you will not see these.

## Word and segment timings

Pass `timestamps` to get alignment data — useful for subtitles, or for lining
a transcript up against the audio:

```python
result = khaya.transcribe("recording.wav", "twi", timestamps="word")

for word in result.timings.words:
    print(f"{word.start:.2f}-{word.end:.2f}  {word.word}")
#  0.00-0.12  Me
#  0.12-0.26  ho
#  0.26-0.52  yɛ.
```

`timestamps="segment"` populates `result.timings.segments` instead, each with
`text`, `start` and `end`. Offsets are in seconds. Without `timestamps`,
`result.timings` is `None`.

## API version

The SDK calls ASR v3. v1 returns a bare string and supports neither warnings
nor timings; pin it with `Settings(asr_version="v1")` if you need the old
behaviour.

## Supported languages

34 languages — see the [language reference](../languages.md#asr-languages).
ASR and TTS use different codes for some languages, so check the right table.

## Audio requirements

- **Format:** WAV (`.wav`)
- **Encoding:** PCM (uncompressed)
- **Sample rate:** 16 kHz recommended
- **Channels:** Mono

Convert to the correct format with ffmpeg if needed:

```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

## Saving the transcript

```python
with KhayaClient(api_key) as khaya:
    result = khaya.transcribe("speech.wav", "twi")
    with open("transcript.txt", "w") as f:
        f.write(result.text)
```

## Error handling

```python
from khaya.exceptions import ASRTranscriptionError, AuthenticationError, APIError

try:
    result = khaya.transcribe("speech.wav", "twi")
except ASRTranscriptionError as e:
    # Raised when the file is not found or input is invalid
    print(f"Transcription error: {e.message}")
except AuthenticationError:
    print("Check your API key.")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

See [Error Handling](error-handling.md) for the full exception reference.
