# Khaya SDK — Clean Code Principles

These principles govern all contributions to the khaya-sdk codebase.

## 1. Exceptions, not Error Returns

Functions must raise exceptions on failure — never return error dicts.
SDK users should be able to use try/except exclusively.
Map HTTP status codes to specific exception types.

## 2. Preserve Exception Chains

Always use `raise SpecificError(...) from original_exception`.
Never lose the original traceback.

## 3. Type Everything

All public function signatures must have complete type hints.
Use `httpx.Response` (not `requests.Response`).
Define TypedDict for structured dicts if dicts must be returned.
Run mypy as part of CI — no type errors allowed.

## 4. No Catch-All Handlers

Only catch what you expect. Let unexpected exceptions propagate.
`except Exception` is forbidden except at the very top level.

## 5. Never Log Secrets

Never log headers, full kwargs, or request bodies.
Only log HTTP method and URL at DEBUG level.
Never `print()` API keys or credentials.

## 6. Follow Naming Conventions

Parameter names must be consistent across all services:
- Language: `language: str`
- Language pair: `language_pair: str`
- Text input: `text: str`

No abbreviations (no `lang`, no `db`).

## 7. Imports Must Be Accurate

Use `httpx.Response` — not `requests.Response`.
Remove all unused imports.
Separate stdlib, third-party, and first-party imports (isort).

## 8. URL Parameters via `params=`

Never build query strings via f-string interpolation.
Use the httpx `params=` argument for query parameters.

## 9. Consistent Payload Construction

Always use `json=dict_payload` for JSON bodies.
Never manually call `json.dumps()` and pass as `data=`.

## 10. SDK Logging Convention

Use `logging.getLogger("khaya")` with `NullHandler()` default.
Let the consuming application configure log levels.
Never call `basicConfig()` in library code.

## 11. Resource Cleanup

Classes that hold external resources (HTTP clients, file handles)
must implement `__enter__` / `__exit__` or an explicit `close()` method.

## 12. Configuration Strictness

Pydantic models must use `extra="forbid"` to catch typos at init.
Validate all config at client creation — fail fast.

## 13. Test with Mocks, Not Live APIs

Unit tests must mock all HTTP calls (use `respx` for httpx).
Tests must pass without network access and without an API key.
Integration tests must be clearly marked and skipped in CI by default.

## 14. One Responsibility Per Class/Function

Services (TranslationService, etc.) only handle request construction + calling.
BaseApi only handles HTTP transport.
Config only manages settings.
No mixed concerns.

## 15. Minimum Public Surface

Only expose what users need. Keep internals private.
Everything in `__all__` must be intentional.
Export exception classes for user convenience.
