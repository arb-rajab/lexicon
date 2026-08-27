"""Heading/section-aware chunking (FR-002).

Adapted from the Session 1 spike's chunk_markdown (docs/spikes/session1-
hybrid-retrieval/spike.py) — same method, now application code instead of a
throwaway script, per this session's task ("Fixed by Session 1's spike",
03-architecture.md).
"""

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$")
_MIN_WORDS = 20


@dataclass
class ChunkCandidate:
    heading: str
    content: str
    position: int


def chunk_markdown(text: str) -> list[ChunkCandidate]:
    lines = text.splitlines()
    chunks: list[ChunkCandidate] = []
    current_heading = "(intro)"
    current_lines: list[str] = []
    position = 0

    def flush() -> None:
        nonlocal position
        body = "\n".join(current_lines).strip()
        if body and len(body.split()) >= _MIN_WORDS:
            chunks.append(ChunkCandidate(heading=current_heading, content=body, position=position))
            position += 1

    for line in lines:
        match = _HEADING_RE.match(line)
        if match:
            flush()
            current_heading = match.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()

    return chunks
