# Speech Recognition (ASR)

Transcribe spoken audio to text using `transcribe()` or `atranscribe()`.

## Basic usage

```python
from khaya import KhayaClient

with KhayaClient(api_key) as khaya:
    result = khaya.transcribe("recording.wav", "tw")
    print(result.json())  # "me ho yɛ"
```

The second argument is the **language code** of the spoken language in the audio.

## Supported languages

| Code | Language |
|------|----------|
| `tw` | Twi |
| `gaa` | Ga |
| `dag` | Dagbani |
| `ee` | Ewe |
| `dga` | Dagaare |
| `fat` | Fante |
| `gur` | Gurene |
| `nzi` | Nzema |
| `kpo` | Ghanaian Pidgin |
| `yo` | Yoruba |

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
    result = khaya.transcribe("speech.wav", "tw")
    transcript: str = result.json()
    with open("transcript.txt", "w") as f:
        f.write(transcript)
```

## Error handling

```python
from khaya.exceptions import ASRTranscriptionError, AuthenticationError, APIError

try:
    result = khaya.transcribe("speech.wav", "tw")
except ASRTranscriptionError as e:
    # Raised when the file is not found or input is invalid
    print(f"Transcription error: {e.message}")
except AuthenticationError:
    print("Check your API key.")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

See [Error Handling](error-handling.md) for the full exception reference.
