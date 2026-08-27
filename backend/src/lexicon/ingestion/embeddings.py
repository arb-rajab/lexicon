"""Embedding generation — BAAI/bge-small-en-v1.5 via fastembed (ONNX, no
torch dependency), matching the Session 1 spike exactly (RESULTS.md Setup).
This is a local model: it needs no LLM provider credentials, so ingestion
and retrieval work fully today regardless of the ANTHROPIC_API_KEY
situation (only generation/verification, in llm/, are blocked on that).
"""

from functools import lru_cache

from fastembed import TextEmbedding

from lexicon.config import get_settings


@lru_cache
def _model() -> TextEmbedding:
    settings = get_settings()
    return TextEmbedding(model_name=settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return [e.tolist() for e in _model().embed(texts)]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
