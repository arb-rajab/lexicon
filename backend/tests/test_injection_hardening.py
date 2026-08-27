"""ADR-0003: the generator (T-01) and verifier (T-02) must carry genuinely
different injection-hardening implementations, not the same mitigation
copy-pasted to both call sites. These tests assert the structural
differences directly against the prompt-builders and schemas, not just
against behavior — a shared-mitigation regression should fail here even if
it happens not to change any single test's pass/fail outcome elsewhere.
"""

import uuid

from lexicon.llm.base import VerificationVerdict
from lexicon.llm.prompts import (
    _UNTRUSTED_WARNING,
    GENERATION_SYSTEM_PROMPT,
    build_generation_user_content,
    build_verification_user_content,
)
from lexicon.llm.schemas import GenerationOutput, VerificationOutput
from lexicon.pipeline.query_pipeline import _ClaimVerdict
from lexicon.retrieval.service import RetrievedChunkContext


def _sample_chunk() -> RetrievedChunkContext:
    return RetrievedChunkContext(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        source_filename="x.md",
        section_heading="Heading",
        content="Some passage content.",
        fusion_rank=1,
        fusion_score=1.0,
        keyword_rank=1,
        vector_rank=1,
    )


def test_verifier_prompt_sandwiches_the_untrusted_warning() -> None:
    # ADR-0003 item 2: the warning must appear both BEFORE and AFTER the
    # passage, bracketing it — not once.
    content = build_verification_user_content("claim", "passage text")
    first = content.find(_UNTRUSTED_WARNING)
    second = content.find(_UNTRUSTED_WARNING, first + 1)
    assert first != -1
    assert second != -1
    assert second > first

    passage_start = content.find("<<<PASSAGE_START>>>")
    passage_end = content.find("<<<PASSAGE_END>>>")
    assert first < passage_start < passage_end < second


def test_generator_prompt_does_not_sandwich_reference_material() -> None:
    # T-01's mitigation is a single delimited block, not a sandwich — the
    # generator relies on independent verification as its backstop rather
    # than needing the sandwiched-repetition defense (06-security-threat-
    # model.md's "why the verifier's defense is structurally different").
    content = build_generation_user_content("question", [_sample_chunk()])
    assert content.count("<reference_material>") == 1
    assert content.count("</reference_material>") == 1
    assert GENERATION_SYSTEM_PROMPT.lower().count("untrusted") == 1


def test_verification_schema_has_no_free_text_field() -> None:
    # ADR-0003 item 1: exactly two booleans, no surface for the model to
    # narrate compliance with an injected instruction.
    assert set(VerificationOutput.model_fields.keys()) == {"entailed", "injection_suspected"}


def test_generation_and_verification_schemas_are_different_shapes() -> None:
    generation_fields = set(GenerationOutput.model_fields.keys())
    verification_fields = set(VerificationOutput.model_fields.keys())
    assert generation_fields != verification_fields
    # Only the verifier gets the injection_suspected self-report signal —
    # the generator's defense doesn't need it (it isn't the backstop).
    assert "injection_suspected" not in generation_fields


def test_pipeline_enforces_injection_suspected_auto_fail_regardless_of_entailed() -> None:
    # ADR-0003 item 3, enforced in application code (pipeline/
    # query_pipeline.py), not merely requested of the prompt: a model that
    # reports entailed=True but injection_suspected=True must still gate to
    # enforced_entailed=False.
    verdict = _ClaimVerdict(
        claim_text="x",
        chunk=_sample_chunk(),
        raw_verdict=VerificationVerdict(entailed=True, injection_suspected=True),
    )
    assert verdict.enforced_entailed is False


def test_pipeline_does_not_auto_fail_when_injection_not_suspected() -> None:
    verdict = _ClaimVerdict(
        claim_text="x",
        chunk=_sample_chunk(),
        raw_verdict=VerificationVerdict(entailed=True, injection_suspected=False),
    )
    assert verdict.enforced_entailed is True
