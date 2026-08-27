"""Selects the LLM client tier — the AppServiceProvider-binding counterpart
in bookslot's pattern. Real credentials in, real client out; nothing
configured, stub client out. See docs/project-memory/12-session-handoff.md
for why this is a config decision, not a code branch application code ever
needs to know about (pipeline/query_pipeline.py depends only on the
LLMClient protocol).
"""

from lexicon.config import Settings, get_settings
from lexicon.llm.anthropic_client import AnthropicLLMClient
from lexicon.llm.base import LLMClient
from lexicon.llm.stub_client import StubLLMClient


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    settings = settings or get_settings()
    if settings.anthropic_api_key:
        return AnthropicLLMClient(
            api_key=settings.anthropic_api_key,
            generation_model=settings.generation_model,
            verification_model=settings.verification_model,
        )
    return StubLLMClient()
