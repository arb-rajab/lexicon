# Case Study: lexicon

> An honest account of building a grounded document Q&A (RAG) system over
> seven sessions — what a real measurement changed about the design, what
> a deliberate scope decision permanently cost, and the bugs found by
> actually running the thing rather than trusting that it would work.
> Written from the real spike results, ADRs, and session handoffs linked
> throughout; nothing here is asserted without a pointer to the record
> that backs it.

## What this is

[lexicon](../README.md) is a self-hostable document Q&A system built
around one hard product invariant: every answer is shown to the user only
alongside the specific passage it was grounded in, or the system refuses
to answer (`docs/project-memory/00-project-brief.md`). It is a portfolio
build, not a funded product — see the ADR-0004 section below for what
that meant in practice, in more detail than a portfolio disclaimer
usually gets.

The two SDLC phases this repository is built to demonstrate *deeply*
are Discovery & Planning and Verification & Testing
(`docs/SDLC-EVIDENCE.md`) — not because the other phases were skipped,
but because those two carry the evidence for the two claims this project
actually exists to prove: that retrieval confidence alone can't safely
gate a refusal decision, and that the mechanism built to fix that is
tested as a real security control, not assumed to work.

## The core engineering story: a measurement that changed the architecture

Session 1 was a feasibility spike, not implementation — eight pages of
real FastAPI documentation, chunked, embedded, indexed into a real
pgvector instance, and queried with eleven hand-written test queries
(`docs/spikes/session1-hybrid-retrieval/RESULTS.md`). The plan going in
was to prove hybrid retrieval worked end-to-end. It did — keyword search
(OR semantics), vector search, and RRF fusion each hit 9/9 (100%)
recall@3 on the nine genuinely answerable queries. That result was
expected.

What wasn't expected was the second finding, run as a matter of spike
hygiene rather than because anyone predicted it would matter: two
negative-control queries had no correct answer anywhere in the corpus.
One was fully unrelated ("What is the boiling point of tungsten?",
0.515 top similarity — cleanly separable from every correct answer). The
other was topically adjacent but absent: *"How do I set up 'Sign in with
Google' as an OAuth2 identity provider?"* scored **0.701** — squarely
inside the **0.706–0.848** range the nine genuinely correct answers
scored. The corpus's OAuth2/JWT password-flow chunk shares enough
vocabulary with "OAuth2 identity provider" to score as if it were a real
match, despite never once mentioning Google or third-party sign-in.

This is the moment that decided the rest of the project's architecture.
A similarity-threshold refusal rule — "refuse below 0.6," or any fixed
cutoff — would have handed that chunk to generation with high confidence
and risked a fabricated-but-plausible answer about a feature the
documentation never covers. That is not a hypothetical failure mode
invented to justify a design; it is a number that came out of a real run
against real infrastructure, on the first day of the project, before any
refusal mechanism existed to protect against it.

[ADR-0001](adr/ADR-0001-groundedness-refusal-check.md) is the direct
answer to that number, not a feature planned from the start. It rejects
two options that share the same underlying shape as the mechanism the
spike just disproved — a cross-encoder reranker (still a soft numeric
relevance score, still answering "is this topically related" rather than
"does this specific passage support this specific claim") and a
pre-generation LLM judge (asked to grade relevance against the *question*
before any candidate answer exists, which reproduces the identical
topical-adjacency trap a human skimming the OAuth2/JWT chunk would fall
into). What it commits to instead is post-generation
groundedness/entailment verification: generation must cite specific
chunks and self-refuse when the passages don't support an answer, and an
independent LLM call — one that never sees the generator's own reasoning
— checks each cited claim against the exact text of its cited passage.
The self-refusal is a cheap first filter; the independent verification
is what the "cited or refused" invariant is actually enforced by, because
a generator can be wrong about its own certainty and a second call
grading the first call's homework inside the same context window
wouldn't catch that.

## The injection-hardening story: two call sites, two defenses, and why one matters more

ADR-0001 built a mechanism the whole system depends on — which is exactly
why its own Consequences section named a task for the next security
session: prove the verification step resists a passage that tries to
talk it into agreeing with a false claim, don't just assume it would.
[ADR-0003](adr/ADR-0003-verification-injection-hardening.md) is that
work, and it treats the generator and the verifier as two structurally
different attack surfaces rather than one problem solved twice.

The generator's context is noisy — the top-5 retrieved chunks plus the
user's query, where one attacker-controlled chunk has to compete for
influence with several others. The verifier's context, per claim, is
exactly one passage the generator already cited. That passage is not
something an attacker merely hopes gets retrieved — if a poisoned
document's chunk survived retrieval and got cited, its exact text is
*guaranteed* to reach the verifier, verbatim, because reading it exactly
as written is the verifier's whole job. And there is no third check: if
the verifier is hijacked into reporting `entailed: true` for a claim its
passage doesn't actually support, the pipeline releases the answer, and
every downstream signal — the API response, the `CITATION_VERDICT` row
itself — reports that verification passed. This is why ADR-0003 names T-02
(verifier hijack) as the more severe of the two named threats, distinct
from T-01 (generator hijack): it is the last line of defense the entire
system leans on, and a defeated verifier doesn't degrade gracefully, it
silently defeats the invariant while looking like it worked.

The hardening itself is four elements adopted together, not as optional
add-ons: forced structured output (`{entailed, injection_suspected}`,
no free-text surface for an injected instruction to narrate through),
sandwiched delimiting (the untrusted-content warning stated both before
*and* after the passage, not just once), an explicit
`injection_suspected` self-report that the application layer forces to
`entailed: false` regardless of the model's own judgment, and fail-closed
on any unparseable or ambiguous response.

Session 6 built the adversarial corpus this design had been waiting on —
18 real documents across four categories, ingested through the real
pipeline into their own isolated corpus
(`docs/security/adversarial-corpus/`). It measured two genuinely
different things, reported separately rather than blended into one
pass/fail number:

- **Structural containment: 18/18.** The delimiting and the
  `injection_suspected → enforced_entailed=False` override both held
  across all 18 documents, checked against real `CITATION_VERDICT`
  database rows, not asserted from a canned example. This number is a
  code-level guarantee — pure string construction and an unconditional
  override, provable regardless of model tier, because no model judgment
  is involved in either check.
- **Category 4 false-positive rate: 50% (2/4).** Two legitimate documents
  that genuinely *discuss* or *quote* injection-attack phrasing as their
  actual subject matter were flagged as suspicious anyway. This is a
  real, measured limit of `StubLLMClient`'s detection — ten hardcoded
  substring markers with no contextual understanding — reported honestly
  rather than rounded away, precisely so the 18/18 number above doesn't
  read as more than it is. The corpus's own README
  (`docs/security/adversarial-corpus/README.md`) states plainly what the
  18/18 and the 50% each do and don't prove, and neither number is
  allowed to stand in for the other.

## The ADR-0004 arc

This is the most differentiated part of this project, and it deserves to
be told straight rather than summarized into a caveat line.

Every session from Session 2 onward flagged the same gap: no
`ANTHROPIC_API_KEY` exists in this environment. Session 4 went further
and argued, correctly, that this gap is not like `bookslot`'s
permanently-descoped Stripe credential — it called obtaining a real key
"an urgent, cheap-to-clear blocker," the single gating action before any
real evidence about the system could exist. That framing was right about
the stakes and wrong about the outcome: the project owner made a
deliberate, permanent choice not to obtain a real Anthropic API key for
this project's lifecycle, for portfolio/skill-proof reasons
([ADR-0004](adr/ADR-0004-real-llm-verification-descoped.md)).

ADR-0004 is explicit that this is not the same severity as `bookslot`'s
Stripe decision or `privacy-forge`'s live-demo descoping. In `bookslot`,
the untested integration (real Stripe responses) was not the
differentiating claim that project existed to prove — double-booking
prevention under real concurrent load was proven independently, without
Stripe. In `lexicon`, the undemonstrated piece **is** the differentiating
claim. The whole point of ADR-0001 is that a real model's entailment
reasoning can do what a similarity threshold measurably cannot (the 0.701
number above). The whole point of ADR-0003 is that the verification call
resists a passage trying to manipulate it. Neither of those two things
can ever be observed against a real model in this project's current
lifecycle, once ADR-0004 is in effect. Any description of this
repository's verification mechanism as "proven" or "validated" against
real model behavior is, after ADR-0004, describing something the project
made permanently impossible to claim honestly.

What that decision cost, precisely: Session 5's evaluation harness could
no longer measure real refusal quality, real citation accuracy, or real
prompt-injection resistance — the ceiling on what those three success
metrics can ever show, for the life of this project, dropped from
"measured" to "the methodology exists and would produce a real number the
moment credentials exist."

What stayed genuinely real despite that: retrieval recall@k never calls
an LLM provider at all, so it remained a fully real, fully measured
metric — Session 5 measured it at **9/9 (100%)** against the real Session
1 corpus, unaffected by ADR-0004 in any way. The full pipeline —
ingestion, hybrid retrieval, generation, verification, refusal gating —
is real, correctly wired application code, proven end-to-end against a
real Postgres+pgvector instance in a growing suite of backend tests, run
against `StubLLMClient`, a client whose behavior (a keyword-overlap
heuristic) is fully documented and fully known, not a black box being
mistaken for a real model. Session 5's refusal-correctness and
citation-accuracy numbers — **11/16 (68.75%)** and **7/10 (70%)** — are
real measurements of *this harness correctly scoring a known,
deterministic behavior*, not of real refusal or citation quality; the
mismatches concretely reproduce Session 1's exact failure shape (the
stub's crude heuristic false-positived on 3 of 5 adjacent-but-wrong
cases), which is itself evidence the golden dataset has real
discriminating power rather than being all easy cases. ADR-0003's
structural hardening and Session 6's 18/18 containment result are, as
described above, code-level guarantees independent of model tier. The
credential-swap seam (`llm/factory.py`) was built once, at Session 4, and
re-confirmed working against the actual production image at Session 7 —
setting the environment variable is a config change, not a rewrite,
should this decision ever be revisited.

Framed the way this developer's other portfolio decisions are framed —
`privacy-forge`'s live-demo descoping, `bookslot`'s Stripe
descoping — this is a real judgment call made under a real, named
constraint (ongoing per-query LLM spend with no revenue behind it, for
work that exists to demonstrate skill rather than operate for real), not
a failure to finish something. The difference from those two precedents,
stated as plainly as ADR-0004 itself states it: this is the one place in
this developer's portfolio where the descoped piece is the central
thesis the project was built to prove, not an integration boundary
alongside an independently-proven core claim. That asymmetry is the
reason ADR-0004 spends most of its own text arguing why it is *not* a
routine, low-stakes scope trim before it commits to the decision anyway.

## Real bugs found and fixed

A feature list is a weaker signal than the bugs a project found in
itself. Four are worth detail here, and they share something worth
naming explicitly before getting into any one of them: **none of the
four were visible in the dev environment or the existing test suite —
only once conditions actually resembled production did any of them
surface.**

**1. AND-semantics keyword search returned zero results for every
answerable query (Session 1).** The first spike run used Postgres's
default `plainto_tsquery`, which ANDs every non-stopword term together.
Natural questions like "What class do I import to add CORS support in
FastAPI?" rarely have every one of their content words — class, import,
add, cors, support, fastapi — co-occurring in one short documentation
chunk, so the query returned **0/9 (0%)** recall@3, not "ranked poorly,"
zero matches. Switching to OR semantics (`to_tsquery` joined with `|`,
ranked by `ts_rank`) fixed it completely, to 9/9 (100%). This became a
concrete, checkable implementation constraint from that day forward — the
AND variant must not ship — not a vague "consider tsquery options" note,
and it's permanently regression-guarded in the backend test suite.

**2. An `async def` upload route blocked the event loop under real
concurrency (Session 7).** `api/documents.py`'s `upload_document` called
the synchronous, CPU-bound `ingest_document` inline. Under dev's bare
`uvicorn --reload`, nothing exposed this. Under `Dockerfile.prod`'s
gunicorn, blocking the event loop for the duration of a real upload
blocked the worker's heartbeat to the arbiter — which killed the worker
mid-upload (`WORKER TIMEOUT`, `SIGABRT`), observed directly, twice, in
container logs before being diagnosed. Fixed via
`starlette.concurrency.run_in_threadpool`; the full 35-test backend suite
was re-run and confirmed still passing after the change.

**3. The first real embedding call triggered a live model download inside
the request path (Session 7).** The same first real upload also fired a
live ~20-30 second HuggingFace fetch (`Fetching 5 files: 100%|...`,
observed directly in container logs), compounding bug 2 and adding a live
external network dependency to every cold-started container's first
request. Fixed by pre-warming `BAAI/bge-small-en-v1.5` into the image at
build time (`EMBEDDING_CACHE_DIR`) — confirmed by re-running the full
8-document ingestion with no further worker timeouts and no HuggingFace
fetch log lines.

**4. Docker's auto-injected `HOSTNAME` broke the frontend's own
healthcheck (Session 7).** The `frontend` container reported Docker
health `unhealthy` continuously — `FailingStreak: 132` after 31 hours —
while serving real traffic correctly over its published port. Root
cause: Docker injects `HOSTNAME=<container id>` into every container, and
Next's standalone `server.js` binds to `process.env.HOSTNAME` if set,
resolving it to the container's one assigned IP rather than all
interfaces — so the healthcheck's own loopback `fetch('http://
localhost:3000/...')`, run from inside that same container,
connection-refused on every cycle. Fixed by pinning `HOSTNAME=0.0.0.0`
explicitly in both the compose file and the Dockerfile itself, confirmed
by watching Docker's own reported status flip from `unhealthy` to
`healthy` after recreating the container.

The common thread across all four: dev environments and unit test suites
don't exercise real concurrency, real cold-start conditions, or a real
container orchestrator's health-checking and process-supervision
behavior. Each of these bugs required actually running the system the
way it would really run to find.

## What this project can and cannot honestly claim

Stated once more, plainly, so it can't be missed by reading only the
sections above.

**Proven, against real infrastructure:** hybrid retrieval end-to-end
against a real corpus and real pgvector (9/9 recall@3, both at the
Session 1 spike and again in Session 5's evaluation harness); the full
ingest → retrieve → generate → verify → refuse pipeline, wired correctly
and tested against a real Postgres+pgvector instance; the database-level
audit-trail permission split (ADR-0002), checked against a real
connection using the restricted runtime role; ADR-0003's structural
injection hardening — forced structured output, sandwiched delimiting,
the enforced override, fail-closed on ambiguity — as code-level
guarantees independent of model tier, checked against 18 real documents
with 18/18 containment and zero override violations; the credential-swap
seam, re-confirmed against the actual production image; and a
production-shaped deployment (real Dockerfiles, a real five-service
compose stack, real HTTP traffic through it) with three real bugs found
and fixed in the process.

**Permanently unprovable, by deliberate choice (ADR-0004):** whether a
real model's entailment reasoning actually catches a topically-adjacent
but wrong claim — the exact 0.701-scoring OAuth2/JWT case this project's
whole refusal architecture exists to handle — and whether ADR-0003's
hardening actually resists a passage that tries to manipulate a real
verifier's judgment. Every number in this document that looks like a
quality measurement (refusal-correctness, citation-accuracy, the stub's
marker-detection rate, its false-positive rate) is a measurement of the
harness correctly scoring `StubLLMClient`'s known, deterministic
behavior — not a measurement of real model quality, and not described as
one anywhere in this repository since ADR-0004, on purpose.

## Where this stands

Seven sessions in: Discovery (Session 1), Requirements and Architecture
including three ADRs (Sessions 2-3), Implementation (Session 4),
Verification and Testing reframed around ADR-0004's boundary (Session 5),
the adversarial injection corpus (Session 6), and production-shaped
deployment proof (Session 7). See
[`docs/project-memory/12-session-handoff.md`](project-memory/12-session-handoff.md)
for the full session-by-session account, and
[`docs/SDLC-EVIDENCE.md`](SDLC-EVIDENCE.md) for the phase-by-phase
evidence map this case study draws from.
