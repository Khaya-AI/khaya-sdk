"""Guards against documentation drifting away from the public API.

The README quick start once demonstrated ``result.json()`` and
``result.content`` — the pre-typed-result API — for several releases after
those attributes were removed. Nothing executed the documented examples, so
nothing caught it. These tests are cheap structural checks, not a substitute
for running the examples, but they catch that whole class of rot.
"""

import re
from pathlib import Path

import pytest

from khaya.constants import (
    SUPPORTED_ASR_LANGUAGES,
    SUPPORTED_LANGUAGE_PAIRS,
    SUPPORTED_TTS_LANGUAGES,
    SUPPORTED_TTS_SPEAKERS,
)
from khaya.models import SynthesisResult, TranscriptionResult, TranslationResult

REPO_ROOT = Path(__file__).resolve().parent.parent

DOC_FILES = [
    REPO_ROOT / "README.md",
    *sorted((REPO_ROOT / "docs").rglob("*.md")),
]

# Attributes that only ever existed on httpx.Response. If a doc calls one of
# these on a `result`, it is describing an API the SDK no longer has.
REMOVED_RESULT_ATTRS = ("json()", "content", "status_code")


def _python_blocks(markdown: str) -> list[str]:
    return re.findall(r"```python\n(.*?)```", markdown, re.DOTALL)


@pytest.mark.parametrize("path", DOC_FILES, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_docs_do_not_use_removed_result_attributes(path: Path):
    offenders = []
    for block in _python_blocks(path.read_text(encoding="utf-8")):
        for lineno, line in enumerate(block.splitlines(), 1):
            for attr in REMOVED_RESULT_ATTRS:
                # `result.json()` is wrong; `e.status_code` on an exception is fine.
                if re.search(rf"\bresult\.{re.escape(attr)}", line):
                    offenders.append(f"  line {lineno}: {line.strip()}")

    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} documents attributes the result objects "
        f"do not have:\n" + "\n".join(offenders)
    )


def test_documented_result_attributes_exist():
    """The attributes the docs tell users to reach for must actually exist."""
    assert {"text", "source_language", "target_language"} <= set(
        TranslationResult.__dataclass_fields__
    )
    assert {"text", "language"} <= set(TranscriptionResult.__dataclass_fields__)
    assert {"audio", "language"} <= set(SynthesisResult.__dataclass_fields__)
    assert callable(SynthesisResult.save)


# ---------------------------------------------------------------------------
# docs/languages.md is the single source for language reference data. These pin
# it to khaya.constants so the two cannot drift — the failure mode that put
# nine non-existent ASR codes in the docs for several releases.
# ---------------------------------------------------------------------------

LANGUAGES_PAGE = REPO_ROOT / "docs" / "languages.md"


def _table_codes(heading: str) -> set[str]:
    """Return the `code` column of the table under a `## heading`."""
    body = LANGUAGES_PAGE.read_text().split(f"## {heading}", 1)[1]
    body = body.split("\n## ", 1)[0]
    return set(re.findall(r"^\| `([^`]+)` \|", body, re.MULTILINE))


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("Translation pairs", SUPPORTED_LANGUAGE_PAIRS),
        ("ASR languages", SUPPORTED_ASR_LANGUAGES),
        ("TTS languages", SUPPORTED_TTS_LANGUAGES),
        ("TTS speakers", SUPPORTED_TTS_SPEAKERS),
    ],
)
def test_languages_page_matches_constants(heading, expected):
    assert _table_codes(heading) == set(expected)


def test_guides_link_to_the_languages_page_rather_than_copying_it():
    """A second copy of a table is a second thing to forget to update.

    Detects the table itself, not passing mentions of a code in prose.
    """
    signatures = ("| Code | Language |", "| Pair | Direction |")
    for doc in DOC_FILES:
        if doc.name == "languages.md":
            continue
        text = doc.read_text()
        for signature in signatures:
            assert signature not in text, f"{doc.name} carries a copy of a language table"
