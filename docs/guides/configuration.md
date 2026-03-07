# Configuration

`KhayaClient` accepts an optional `Settings` object for fine-grained control over timeouts, retries, and the API base URL.

## Defaults

| Setting | Default | Description |
|---------|---------|-------------|
| `api_key` | `None` | Your Khaya API key |
| `base_url` | `https://translation-api.ghananlp.org` | API base URL |
| `timeout` | `30` | Request timeout in seconds |
| `retry_attempts` | `3` | Number of attempts on transient failures |

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

## Retry behaviour

The SDK retries automatically on:

- `429 Too Many Requests` (honoring `Retry-After` header if present)
- `500`, `502`, `503`, `504` server errors
- Network/transport errors (connection refused, DNS failure, etc.)

**401 Unauthorized** is never retried.

Retries use exponential backoff with jitter: `delay = 2^attempt + random(0, 1)` seconds.

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
