# Releasing

`dev` collects changes. `main` always matches what is on PyPI. Releases are cut
by [release-please](https://github.com/googleapis/release-please) on `main`.

## Commit messages

release-please reads [Conventional Commits](https://www.conventionalcommits.org)
on `main` to pick the version and write the changelog:

- `fix:` → patch, `feat:` → minor.
- `feat!:` or a `BREAKING CHANGE:` footer → minor while on 0.x, major after.
- `docs:` and `deps:` appear in the changelog; `build:`, `ci:`, `chore:`,
  `test:`, `refactor:` don't.

Squash-merge feature PRs into `dev` with a conventional PR title. To fix the
changelog for an already-merged PR, add to its description:

```
BEGIN_COMMIT_OVERRIDE
feat!: move the SDK to the Khaya platform
END_COMMIT_OVERRIDE
```

## Release

1. Run the integration tests against the live API:
   `KHAYA_API_KEY=... uv run pytest -m integration`.
2. Open a PR from `dev` to `main` titled `release: dev to main`. Merge it with a
   merge commit, not a squash, so the conventional commits reach `main`.
3. release-please opens (or updates) a `chore(main): release X.Y.Z` PR that
   bumps `pyproject.toml` and `uv.lock` and adds the changelog section. Edit its
   `CHANGELOG.md` if the notes need prose; do it last, since every push to
   `main` regenerates the PR.
4. Merge the release PR. release-please tags `vX.Y.Z` and creates the GitHub
   release; the tag runs `release.yml`, which tests, publishes to TestPyPI and
   PyPI (after approval on the `pypi` environment), and attaches the dist files.
5. Merge `main` back into `dev`.

To force a version, add a `Release-As: X.Y.Z` footer to a commit on `main`.

Rehearse with **Actions → Release to PyPI → Run workflow → testpypi** on any branch.

## Hotfix

1. Branch from `main`, commit the fix as `fix: ...`, and PR into `main`.
2. Merge the release PR release-please opens.
3. Merge `main` back into `dev`.

## Setup

release-please authenticates as a GitHub App, because tags pushed with
`GITHUB_TOKEN` don't trigger `release.yml`. The app needs **Contents**,
**Pull requests** and **Issues** (labels) read/write on this repo. Store its ID
as the `RELEASE_PLEASE_APP_ID` Actions variable and its private key as the
`RELEASE_PLEASE_PRIVATE_KEY` secret.

## Versioning

[SemVer](https://semver.org). While on 0.x, a breaking change bumps the minor
version and needs a migration note in the changelog.
