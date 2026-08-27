from lexicon.ingestion.chunking import chunk_markdown

SAMPLE = """# Intro heading

This is the introductory section with plenty of words padded out so it
clears the twenty word minimum threshold used to drop trivial chunks like
pure code fences.

## Second section

This is the second section, also padded with enough words to survive the
minimum-word-count filter applied during chunking so it becomes a real
chunk candidate.

## Tiny

Too short.
"""


def test_chunk_markdown_splits_on_headings_and_drops_trivial_chunks() -> None:
    chunks = chunk_markdown(SAMPLE)

    headings = [c.heading for c in chunks]
    assert "Intro heading" in headings
    assert "Second section" in headings
    assert "Tiny" not in headings  # below the 20-word minimum


def test_chunk_markdown_assigns_sequential_positions() -> None:
    chunks = chunk_markdown(SAMPLE)
    assert [c.position for c in chunks] == list(range(len(chunks)))
