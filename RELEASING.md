# Releasing

`dev` collects changes. `main` always matches what is on PyPI. A release is a
`dev` → `main` PR followed by a tag.

## Release

1. On a branch from `dev`, bump `version` in `pyproject.toml`, run `uv lock`,
   and move `[Unreleased]` in `CHANGELOG.md` to `## [X.Y.Z] — YYYY-MM-DD`.
   Merge into `dev`.
2. Run the integration tests against the live API:
   `KHAYA_API_KEY=... uv run pytest -m integration`.
3. Open a PR from `dev` to `main` titled `release: X.Y.Z`. Merge it with a merge
   commit, not a squash.
4. Tag the merge commit on `main` and push it:

   ```bash
   git checkout main && git pull
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

5. `release.yml` tests, publishes to TestPyPI and PyPI (after approval on the
   `pypi` environment), and creates the GitHub release.

Rehearse with **Actions → Release to PyPI → Run workflow → testpypi** on any branch.

## Hotfix

1. Branch from `main`, fix, bump the patch version, and add a changelog entry.
2. PR into `main`, merge, and tag as above.
3. Merge `main` back into `dev`.

## Versioning

[SemVer](https://semver.org). While on 0.x, a breaking change bumps the minor
version and needs a migration note in the changelog.
