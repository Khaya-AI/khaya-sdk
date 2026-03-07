# Error Handling

All errors in the Khaya SDK are raised as exceptions — never returned as error dicts or status codes. Use standard Python `try/except` to handle them.

## Exception hierarchy

```
Exception
└── APIError                  # base class for all Khaya errors
    ├── AuthenticationError   # 401 — invalid or missing API key
    ├── RateLimitError        # 429 — too many requests
    ├── TranslationError      # bad input to translate()
    ├── TTSGenerationError    # bad input to synthesize()
    └── ASRTranscriptionError # bad input or missing file for transcribe()
```

All exceptions expose two attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Human-readable error description |
| `status_code` | `int` | HTTP status code (0 for transport errors) |

## Catching errors

### Catch the specific exception you expect

```python
from khaya import KhayaClient
from khaya.exceptions import AuthenticationError, RateLimitError, TranslationError, APIError

with KhayaClient(api_key) as khaya:
    try:
        result = khaya.translate("Hello", "en-tw")
    except AuthenticationError:
        # Invalid or missing API key — do not retry
        print("Check your KHAYA_API_KEY.")
    except RateLimitError as e:
        # Too many requests — back off and retry
        print(f"Rate limited: {e.message}")
    except TranslationError as e:
        # Bad input — fix the call, do not retry
        print(f"Bad input: {e.message}")
    except APIError as e:
        # Catch-all for unexpected errors
        print(f"Unexpected error ({e.status_code}): {e.message}")
```

### Import exceptions from the top-level package

All exceptions are available directly from `khaya`:

```python
from khaya import (
    APIError,
    AuthenticationError,
    RateLimitError,
    TranslationError,
    TTSGenerationError,
    ASRTranscriptionError,
)
```

## Common scenarios

### Missing API key

Raised immediately — no HTTP request is made:

```python
client = KhayaClient(api_key="")
client.translate("Hello", "en-tw")  # raises AuthenticationError
```

### File not found (ASR)

```python
try:
    khaya.transcribe("missing.wav", "tw")
except ASRTranscriptionError as e:
    print(e.message)  # "Audio file not found: missing.wav"
```

### Rate limiting

The SDK retries automatically on 429 responses (honouring `Retry-After` if present). If all retries are exhausted, `RateLimitError` is raised:

```python
try:
    result = khaya.translate("Hello", "en-tw")
except RateLimitError as e:
    print(f"Still rate limited after retries: {e.message}")
```

### Transport failures

Network errors (timeouts, DNS failures) are also retried automatically. After all retries fail, an `APIError` is raised with `status_code=0`:

```python
except APIError as e:
    if e.status_code == 0:
        print("Network error — check your connection.")
```

## Retry behaviour

The SDK retries automatically on transient errors (429, 500, 502, 503, 504, and network errors) using exponential backoff with jitter. By default, 3 attempts are made.

Configure retry behaviour via [`Settings`](../api-reference/config.md):

```python
from khaya.config import Settings
from khaya import KhayaClient

config = Settings(api_key=api_key, retry_attempts=5)
client = KhayaClient(api_key=api_key, config=config)
```

401 errors are **never** retried.
