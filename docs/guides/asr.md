# Speech Recognition (ASR)

Transcribe spoken audio to text using `transcribe()` or `atranscribe()`.

## Basic usage

```python
from khaya import KhayaClient

with KhayaClient(api_key) as khaya:
    result = khaya.transcribe("recording.wav", "tw")
    print(result.text)  # "me ho yɛ"
```

The second argument is the **language code** of the spoken language in the audio.

`transcribe()` returns a `TranscriptionResult` with:

| Attribute | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The transcribed string |
| `language` | `str` | Language code of the audio (e.g. `"tw"`) |

## Supported languages

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
    with open("transcript.txt", "w") as f:
        f.write(result.text)
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
