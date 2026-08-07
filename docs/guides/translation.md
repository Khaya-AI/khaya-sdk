# Translation

Translate text between African languages and English using `translate()` or `atranslate()`.

## Basic usage

```python
from khaya import KhayaClient

with KhayaClient(api_key) as khaya:
    result = khaya.translate("Hello, how are you?", "en-tw")
    print(result.text)  # the Twi translation
```

The second argument is the **language pair**: `"<source>-<target>"`.

## Supported language pairs

| Pair | Direction |
|------|-----------|
| `en-tw` | English → Twi |
| `tw-en` | Twi → English |
| `en-ee` | English → Ewe |
| `ee-en` | Ewe → English |
| `en-gaa` | English → Ga |
| `gaa-en` | Ga → English |
| `en-fat` | English → Fante |
| `fat-en` | Fante → English |
| `en-yo` | English → Yoruba |
| `yo-en` | Yoruba → English |
| `en-dag` | English → Dagbani |
| `dag-en` | Dagbani → English |
| `en-ki` | English → Kikuyu |
| `ki-en` | Kikuyu → English |
| `en-gur` | English → Gurune |
| `gur-en` | Gurune → English |
| `en-luo` | English → Luo |
| `luo-en` | Luo → English |
| `en-mer` | English → Kimeru |
| `mer-en` | Kimeru → English |
| `en-kus` | English → Kusaal |
| `kus-en` | Kusaal → English |

!!! note
    The table above is reference data, not a whitelist — the SDK does not validate
    language codes and will send whatever you pass. The API accepts several spellings
    for the same language (`en-tw`, `en-twi` and `eng-twi` all translate to Twi), so
    you can use any pair the API supports without waiting for an SDK release.

    An unsupported pair is rejected by the API with an `APIError` carrying
    `code="VALIDATION_FAILED"` and a `details` entry naming the offending field.

## Translating multiple strings

```python
texts = ["Good morning", "How are you?", "Thank you"]

with KhayaClient(api_key) as khaya:
    results = [khaya.translate(t, "en-tw").text for t in texts]
```

## Checking the response

`translate()` returns a `TranslationResult` with three attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `text` | `str` | The translated string |
| `source_language` | `str` | Source language code (e.g. `"en"`) |
| `target_language` | `str` | Target language code (e.g. `"tw"`) |

```python
print(result.text)            # the translated text
print(result.source_language) # "en"
print(result.target_language) # "tw"
```

## Error handling

```python
from khaya.exceptions import TranslationError, AuthenticationError, APIError

try:
    result = khaya.translate("Hello", "en-tw")
except TranslationError as e:
    print(f"Bad input: {e.message}")
except AuthenticationError:
    print("Check your API key.")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

See [Error Handling](error-handling.md) for the full exception reference.
