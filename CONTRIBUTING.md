# Contributing to khaya-sdk

Thank you for helping improve the Khaya SDK.

## Branching strategy

- `main` — always releasable; protected branch. Every release is tagged here.
- `dev` — integration branch. All work lands here first.
- Feature branches: `feature/<short-description>` (e.g. `feature/add-ki-language`).
- Bug fixes: `fix/<short-description>`.
- Open a PR against `dev`; at least one review is required before merging.
- To release: open a PR from `dev` to `main`, bump `version` in `pyproject.toml`
  and date the `CHANGELOG.md` section, merge, then push a `vX.Y.Z` tag on `main`.
  The tag runs `.github/workflows/release.yml` (tests → TestPyPI → PyPI → GitHub release).

## Commit message format

```
<type>: <short imperative summary>

[optional body — explain what and why, not how]
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`.

Examples:
- `feat: add Kikuyu TTS support`
- `fix: preserve exception chain in ASR file-not-found path`
- `test: add respx mock for 429 rate-limit scenario`

## Running tests locally

```bash
# Install all dependency groups
uv sync --extra test --extra dev

# Run unit tests (no API key required)
uv run pytest -m "not integration"

# Run with coverage report
uv run pytest -m "not integration" --cov=src/khaya --cov-report=term-missing

# Run integration tests (requires KHAYA_API_KEY)
KHAYA_API_KEY=your_key uv run pytest -m integration
```

## Code style

- All rules are enforced by pre-commit hooks (ruff, mypy, isort).
- Install hooks once: `uv run pre-commit install`
- Run against all files: `uv run pre-commit run --all-files`
- See [PRINCIPLES.md](PRINCIPLES.md) for the full coding standards.

## PR checklist

Before opening a PR, confirm:

- [ ] `pre-commit run --all-files` passes with no errors.
- [ ] `pytest -m "not integration"` passes with >= 80% coverage.
- [ ] New public functions have complete type hints and docstrings.
- [ ] No `print()` statements or secrets in any file.
- [ ] `CHANGELOG.md` updated under `[Unreleased]` if user-facing.
