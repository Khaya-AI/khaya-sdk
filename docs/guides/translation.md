# Translation

Translate text between African languages and English using `translate()` or `atranslate()`.

## Basic usage

```python
from khaya import KhayaClient

with KhayaClient(api_key) as khaya:
    result = khaya.translate("Hello, how are you?", "en-tw")
    print(result.json())  # "Ɛte sɛn?"
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
| `en-dag` | English → Dagbani |
| `dag-en` | Dagbani → English |
| `en-dga` | English → Dagaare |
| `dga-en` | Dagaare → English |
| `en-fat` | English → Fante |
| `fat-en` | Fante → English |
| `en-gur` | English → Gurene |
| `gur-en` | Gurene → English |
| `en-nzi` | English → Nzema |
| `nzi-en` | Nzema → English |
| `en-kpo` | English → Ghanaian Pidgin |
| `kpo-en` | Ghanaian Pidgin → English |
| `en-yo` | English → Yoruba |
| `yo-en` | Yoruba → English |
| `en-ki` | English → Kikuyu |
| `ki-en` | Kikuyu → English |

!!! note
    Passing an unknown language pair raises a `UserWarning` but still sends the request.
    This allows you to use new pairs the API supports before the SDK is updated.

## Translating multiple strings

```python
texts = ["Good morning", "How are you?", "Thank you"]

with KhayaClient(api_key) as khaya:
    results = [khaya.translate(t, "en-tw").json() for t in texts]
```

## Checking the response

`translate()` returns an `httpx.Response`. Call `.json()` for the translated string:

```python
result = khaya.translate("Hello", "en-tw")
translated: str = result.json()
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
