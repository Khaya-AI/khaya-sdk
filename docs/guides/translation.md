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

22 pairs across 12 languages, bidirectional with English as the pivot — see the
[language reference](../languages.md#translation-pairs).

!!! note
    That table is reference data, not a whitelist. The SDK does not validate
    language codes and will send whatever you pass. The API accepts several
    spellings for the same language (`en-tw`, `en-twi` and `eng-twi` all
    translate to Twi), so you can use any pair the API supports without waiting
    for an SDK release.

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
