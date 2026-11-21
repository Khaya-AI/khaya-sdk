# Error Handling

All errors in the Khaya SDK are raised as exceptions — never returned as error dicts or status codes. Use standard Python `try/except` to handle them.

## Exception hierarchy

```
Exception
└── APIError                  # base class for all Khaya errors
    ├── AuthenticationError   # 401 — invalid or missing API key
    ├── InsufficientCreditsError  # 402 — credit balance too low for the request
    ├── PayloadTooLargeError  # 413 — request body over the size limit
    ├── UnsupportedMediaTypeError  # 415 — Content-Type not accepted
    ├── RateLimitError        # 429 — too many requests
    ├── ServerError           # 5xx — the platform failed, after retries
    ├── TranslationError      # bad input to translate()
    ├── TTSGenerationError    # bad input to synthesize()
    └── ASRTranscriptionError # bad input or missing file for transcribe()
```

All exceptions expose these attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `message` | `str` | Human-readable error description |
| `status_code` | `int` | HTTP status code (0 for transport errors) |
| `code` | `str \| None` | Machine-readable API error code, e.g. `"VALIDATION_FAILED"` |
| `details` | `list[dict]` | Per-field details, each with `code`, `message`, and `target` |
| `activity_id` | `str \| None` | Server-side correlation ID (the platform's `request_id`, or the `X-Khaya-Request-Id` header when the body has none) — quote this when reporting a problem |

`str(exc)` combines all of them; `exc.message` stays the bare API message.

### Using the structured fields

```python
from khaya.exceptions import APIError

try:
    khaya.translate("Hello", "en-zz")
except APIError as e:
    if e.code == "VALIDATION_FAILED":
        for detail in e.details:
            print(f"{detail['target']}: {detail['message']}")
        # language_pair: Language combination en-zz cannot be used
    elif e.activity_id:
        # Server-side failure — include this ID in a support request
        print(f"Khaya failure, activityId={e.activity_id}")
```

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
    InsufficientCreditsError,
    PayloadTooLargeError,
    UnsupportedMediaTypeError,
    RateLimitError,
    ServerError,
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
    khaya.transcribe("missing.wav", "twi")
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

### Out of credits

A request the account's credit balance cannot cover fails with
`InsufficientCreditsError` (HTTP 402). It is not retried — it will keep failing
until the balance is topped up. The message carries the balance, the estimated
cost, and the top-up link:

```python
from khaya import InsufficientCreditsError

try:
    khaya.synthesize("Me ho yɛ", "twi")
except InsufficientCreditsError as e:
    print(e.message)
    # Insufficient credits: balance 3, request costs ~10. Top up at https://...
```

### Request too large

The gateway rejects a body over its size limit with HTTP 413 and the platform
code `REQUEST_TOO_LARGE`. The SDK raises `PayloadTooLargeError` and does not
retry, because the same body will be rejected again. Send less data: split long
text, or trim or compress the audio.

```python
from khaya import PayloadTooLargeError

try:
    khaya.transcribe("long-interview.wav", "twi")
except PayloadTooLargeError as e:
    print(e.code, e.activity_id)  # REQUEST_TOO_LARGE <request id>
```

### Unsupported Content-Type

HTTP 415 with the platform code `UNSUPPORTED_MEDIA_TYPE` raises
`UnsupportedMediaTypeError`, never retried. ASR accepts `audio/*`, `video/*` or
`application/octet-stream`; translation and TTS accept `application/json`. The
SDK sets the right type, so seeing this usually means a proxy or a custom
header changed it.

### Server errors

A 500, 502, 503 or 504 is retried. When the attempts run out the SDK raises
`ServerError`, a subclass of `APIError`, so existing `except APIError` blocks
still catch it. Any other 5xx is raised at once. Include `activity_id` when
you contact support.

### Key not allowed on a route

A key restricted to some services gets a 403 `APIError` with
`code == "ROUTE_NOT_ALLOWED"` on the others. Free anonymous keys that have used
their allowance get `code == "SIGNUP_REQUIRED"`.

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

Other 4xx errors — 401, 402, 403, 413, 415, validation errors — are **never** retried.

## Usage headers

Successful results carry a `usage` object read from the gateway's response
headers: `estimated_credit_cost` (`X-Estimated-Credit-Cost`),
`rate_limit_per_minute` (`X-RateLimit-Limit-Minute`),
`rate_limit_remaining_minute` (`X-RateLimit-Remaining-Minute`),
`free_credits_remaining` (`X-Free-Credits-Remaining`, anonymous keys only),
`request_id` (`X-Khaya-Request-Id`) and `correlation_id` (`X-Correlation-ID`).
Any field is `None` when its header was not sent, and `usage` itself is `None`
when none were.
