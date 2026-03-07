# Async Usage

Every method on `KhayaClient` has an async counterpart prefixed with `a`:

| Sync | Async |
|------|-------|
| `translate()` | `atranslate()` |
| `transcribe()` | `atranscribe()` |
| `synthesize()` | `asynthesize()` |

## Basic example

```python
import asyncio
import os
from khaya import KhayaClient

async def main():
    async with KhayaClient(os.environ["KHAYA_API_KEY"]) as khaya:
        result = await khaya.atranslate("Good morning", "en-tw")
        print(result.json())

asyncio.run(main())
```

Use `async with` to ensure the underlying HTTP client is closed when done.

## Running requests concurrently

The async API is most valuable when you have multiple independent requests — run them in parallel with `asyncio.gather()`:

```python
import asyncio
from khaya import KhayaClient

async def translate_batch(api_key: str, texts: list[str]) -> list[str]:
    async with KhayaClient(api_key) as khaya:
        tasks = [khaya.atranslate(t, "en-tw") for t in texts]
        results = await asyncio.gather(*tasks)
        return [r.json() for r in results]

translations = asyncio.run(translate_batch(api_key, ["Hello", "Goodbye", "Thank you"]))
```

## Mixing services

```python
async def process(api_key: str, text: str, audio_path: str):
    async with KhayaClient(api_key) as khaya:
        translation, transcript = await asyncio.gather(
            khaya.atranslate(text, "en-tw"),
            khaya.atranscribe(audio_path, "tw"),
        )
    return translation.json(), transcript.json()
```

## Error handling

Error handling is identical to the sync API — the same exceptions are raised:

```python
from khaya.exceptions import AuthenticationError, APIError

async with KhayaClient(api_key) as khaya:
    try:
        result = await khaya.atranslate("Hello", "en-tw")
    except AuthenticationError:
        print("Check your API key.")
    except APIError as e:
        print(f"Error {e.status_code}: {e.message}")
```

## Framework integration

=== "FastAPI"

    ```python
    from fastapi import FastAPI
    from khaya import KhayaClient

    app = FastAPI()
    client = KhayaClient(api_key)

    @app.get("/translate")
    async def translate(text: str, pair: str = "en-tw"):
        result = await client.atranslate(text, pair)
        return {"translation": result.json()}
    ```

=== "Django (async view)"

    ```python
    from django.http import JsonResponse
    from khaya import KhayaClient

    async def translate(request):
        text = request.GET.get("text", "")
        async with KhayaClient(api_key) as khaya:
            result = await khaya.atranslate(text, "en-tw")
        return JsonResponse({"translation": result.json()})
    ```

## When to use async vs sync

Use the **async API** when your application is already async (FastAPI, aiohttp, async Django, etc.) or when you need to run multiple Khaya requests concurrently.

Use the **sync API** for scripts, CLIs, and synchronous web frameworks (Flask, Django sync views) — it is simpler and has no additional dependencies.
