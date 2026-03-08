# Logging

The Khaya SDK uses Python's standard `logging` module and follows the recommended library convention: **no handlers are configured by default**, so SDK logs are silent unless you explicitly enable them.

## Enabling logs

Add a handler to the `khaya` logger in your application:

```python
import logging

# Show all DEBUG and above from the SDK
logging.getLogger("khaya").setLevel(logging.DEBUG)
logging.getLogger("khaya").addHandler(logging.StreamHandler())
```

Or use `basicConfig` if you want SDK logs included in your application's root logger:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Logger hierarchy

The SDK uses a separate logger per module, all under the `khaya` namespace:

| Logger | Emits |
|--------|-------|
| `khaya.services.base_api` | HTTP attempts, retries, backoff delays, final responses |
| `khaya.services.translation` | Character count and language pair before each request |
| `khaya.services.asr` | Language, audio file size before each request |
| `khaya.services.tts` | Character count, language, and output audio size |

Setting a handler on `khaya` covers all child loggers automatically. You can also target a specific logger for more granular control:

```python
# Only see retry warnings — suppress DEBUG noise
logging.getLogger("khaya.services.base_api").setLevel(logging.WARNING)
logging.getLogger("khaya.services.base_api").addHandler(logging.StreamHandler())
```

## Log levels

| Level | What the SDK logs |
|-------|------------------|
| `DEBUG` | Every HTTP attempt (attempt N/M), backoff duration, successful response status, file sizes, char counts |
| `WARNING` | Retryable status codes received, transport errors caught, final transport failure before raising |

The SDK never logs at `INFO`, `ERROR`, or `CRITICAL` — errors are communicated via exceptions.

## What is never logged

- API keys or authentication headers
- Request bodies or response bodies
- User text content

## Example output

With `DEBUG` enabled on `khaya.services.base_api`, a request that retries once looks like:

```
DEBUG khaya.services.base_api: HTTP POST https://translation.ghananlp.org/v1/translate (attempt 1/3)
WARNING khaya.services.base_api: Received 500 from POST https://translation.ghananlp.org/v1/translate — retrying (attempt 1/3)
DEBUG khaya.services.base_api: Backing off 1.4s before next attempt
DEBUG khaya.services.base_api: HTTP POST https://translation.ghananlp.org/v1/translate (attempt 2/3)
DEBUG khaya.services.base_api: Response 200: POST https://translation.ghananlp.org/v1/translate
```

## Integrating with structured logging

The SDK is compatible with any standard-compliant logging setup, including structured loggers like [structlog](https://www.structlog.org):

```python
import structlog
import logging

# Route the khaya logger through structlog
logging.getLogger("khaya").addHandler(logging.StreamHandler())
```
