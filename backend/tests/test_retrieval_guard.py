"""FR-005 code-level guard, carried forward since Session 1 (12-session-
handoff.md's risk note): naive AND-semantics keyword search
(`plainto_tsquery`) must never reappear anywhere in the retrieval path —
spike Finding 1 measured it at 0% recall@3 on natural-language questions.
"""

from pathlib import Path

RETRIEVAL_SRC = Path(__file__).resolve().parents[1] / "src" / "lexicon" / "retrieval"


def test_plainto_tsquery_never_appears_in_retrieval_source() -> None:
    # Checks for actual usage (a function call), not the substring alone —
    # keyword.py's own module docstring names `plainto_tsquery` in prose to
    # explain what NOT to use, which must not itself trip this guard.
    offending: list[str] = []
    for path in RETRIEVAL_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "plainto_tsquery(" in text:
            offending.append(str(path))

    assert not offending, (
        "plainto_tsquery(...) call found in retrieval source — this is the exact "
        f"regression spike Finding 1 measured at 0% recall@3: {offending}"
    )


def test_keyword_search_uses_to_tsquery_or_semantics() -> None:
    keyword_src = (RETRIEVAL_SRC / "keyword.py").read_text(encoding="utf-8")
    assert "to_tsquery" in keyword_src
    assert '" | "' in keyword_src or "' | '" in keyword_src
