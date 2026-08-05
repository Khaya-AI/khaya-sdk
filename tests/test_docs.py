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
