# Configuration

`KhayaClient` accepts an optional `Settings` object for fine-grained control over timeouts, retries, and the API base URL.

## Defaults

| Setting | Default | Description |
|---------|---------|-------------|
| `api_key` | `None` | Your Khaya API key |
| `base_url` | `https://api.khaya.ai` | API base URL |
| `timeout` | `30` | Request timeout in seconds |
| `retry_attempts` | `3` | Number of attempts on transient failures |

## Environment variables

Every setting can come from a `KHAYA_`-prefixed environment variable:

| Variable | Sets |
|----------|------|
| `KHAYA_API_KEY` | `api_key` |
| `KHAYA_BASE_URL` | `base_url` |
| `KHAYA_TIMEOUT` | `timeout` |
| `KHAYA_RETRY_ATTEMPTS` | `retry_attempts` |

```python
import os
from khaya import KhayaClient

# KhayaClient still takes the key explicitly:
with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
    ...

# Settings reads the prefixed variables on its own:
from khaya.config import Settings
config = Settings()          # picks up KHAYA_API_KEY, KHAYA_TIMEOUT, ...
```

Unprefixed names like `BASE_URL` are ignored, so an unrelated variable
cannot redirect your API key.

`DevSettings` also reads a local `.env` file:

```python
from khaya.config import DevSettings
config = DevSettings()       # reads ./.env, then the environment
```

## Custom configuration

```python
from khaya import KhayaClient
from khaya.config import Settings

config = Settings(
    api_key="your-key",
    timeout=60,           # longer timeout for slow connections
    retry_attempts=5,     # more retries for unreliable networks
)

with KhayaClient(api_key="your-key", config=config) as khaya:
    result = khaya.translate("Hello", "en-tw")
```

When `config` is provided, the `api_key` argument to `KhayaClient` is ignored — the key from `Settings` is used.

## API version

The Khaya platform publishes one API version, `v1`, for translation, ASR and
TTS, so there is nothing to select. The SDK sends your key as an
`Authorization: Bearer` token and calls:

| Service | Route |
|---------|-------|
| Translation | `/translate/v1/translate` |
| ASR | `/asr/v1/transcribe` |
| TTS | `/tts/v1/synthesize` |

The per-service `translation_version`, `asr_version` and `tts_version` options
from 0.3.x were removed in 0.4.0. Passing one raises a validation error.

## Retry behaviour

The SDK retries automatically on:

- `429 Too Many Requests` (honoring `Retry-After` header if present)
- `500`, `502`, `503`, `504` server errors
- Network/transport errors (connection refused, DNS failure, etc.)

Other 4xx errors are never retried — including **401 Unauthorized** and **402 Insufficient credits**.

All three endpoints are POST and metered, so a 500 the backend actually
processed is retried and billed again. Set `retry_attempts=1` to disable.

Retries use exponential backoff with jitter: `delay = 2^attempt + random(0, 1)` seconds,
capped at 60s. A `Retry-After` header takes precedence and is capped at the same 60s.

## Logging

The SDK is silent by default. To enable logs, add a handler to the `khaya` logger:

```python
import logging
logging.getLogger("khaya").setLevel(logging.DEBUG)
logging.getLogger("khaya").addHandler(logging.StreamHandler())
```

See the [Logging guide](logging.md) for the full logger hierarchy and level reference.

## Validation

`Settings` uses [Pydantic](https://docs.pydantic.dev) for validation. Invalid configuration raises a `ValidationError` at construction time — not at the first API call:

```python
from khaya.config import Settings
from pydantic import ValidationError

try:
    config = Settings(api_key="key", base_url="http://insecure.example.com")
except ValidationError as e:
    print(e)  # base_url must use HTTPS
```

Unknown fields are also rejected:

```python
Settings(api_key="key", typo_field="oops")  # raises ValidationError
```
