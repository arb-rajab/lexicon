# ADR-0002 — Audit Trail Tamper-Evidence: DB-Level Append-Only Enforcement, Not Hash-Chaining

- **Date:** 2026-08-27
- **Status:** accepted

## Context

Session 2 left this question explicitly open, stated verbatim in
`04-data-model.md`'s Revisit trigger section:

> `privacy-forge`'s audit log is hash-chained for tamper-evidence
> (ADR-0003) because its threat model includes an internal actor covering
> up a compliance violation. `lexicon`'s `QUERY_LOG`/`CITATION_VERDICT`
> trail is append-only at the application layer but **not** hash-chained in
> this design — this is a deliberate scope difference, not an oversight:
> `lexicon`'s threat model (`06-security-threat-model.md`, not yet written)
> has not yet established that tamper-evidence of the audit trail itself is
> a required control here, versus append-only-by-convention being
> sufficient for this product's accountability purpose. If the upcoming
> security/threat-model work concludes otherwise, this section should be
> revisited against that finding, not assumed settled by this document.

And, in near-identical terms, `12-session-handoff.md`'s Open questions:

> **Open, not yet decided:** whether `lexicon`'s audit trail
> (`QUERY_LOG`/`CITATION_VERDICT`) needs tamper-evidence (hash-chaining,
> matching `privacy-forge`'s ADR-0003) or whether append-only-by-convention
> is sufficient — explicitly left to the next session's threat model rather
> than decided by default in the data model doc.

This ADR is that resolution.

`QUERY_LOG`/`RETRIEVED_CHUNK`/`CITATION_VERDICT` exist specifically to
serve US-005: "As the accountable party for a wrong answer, I want the
system to log what was retrieved, generated, and verified for each query,
so that a disputed answer can be traced rather than trusted blindly." That
purpose only holds if the trail can be trusted in exactly the scenario it
exists for — a *disputed* answer, where whoever is accountable for it has a
concrete incentive to make the record look better than it was (e.g.
altering a `CITATION_VERDICT.entailed` value from `false` to `true` after
the fact to make a wrongly-released answer look like it had passed
verification). The realistic tamper path is not the application's own
code — `04-data-model.md` already confirms no application code path writes
an update to these tables — but a **privileged database actor**: a
compromised application DB credential, or a person with direct database
access (an operator, an administrator, or, per this threat model's own
insider framing, the very party accountable for the disputed answer).

`privacy-forge`'s ADR-0003 answered a structurally similar-sounding
question with hash-chaining plus external anchoring. That decision was
made against a specific, named driver: an internal actor covering up a
**compliance violation**, in a product whose audit log is a
legal/regulatory-evidentiary artifact (DSAR fulfilment, deletion
certificates, RoPA accuracy) for a data-protection compliance product.
`lexicon` has no equivalent named driver anywhere in its own discovery
documents — `00-project-brief.md`'s stakeholder model, `01-scope-and-non-goals.md`,
and `02-requirements.md`'s data classification table all describe US-005 as
an **internal accountability** mechanism for a self-hosted,
single-operator deployment, not a legal-evidentiary record built against a
named regulator or compliance program. Borrowing `privacy-forge`'s answer
without checking whether the underlying threat driver actually matches
would be pattern-matching to another project's threat model, not reasoning
about this one — which is exactly what this session's ground rules warn
against.

## Options considered

### A — Full hash-chain + external anchoring, matching `privacy-forge`'s ADR-0003

**For:** A proven pattern, already built once elsewhere in this portfolio;
the strongest available tamper-evidence — detects reordering and deletion,
not just field-level edits, and (with anchoring) resists a fully
privileged database actor, not merely a partially privileged one.

**Against:** This is a genuinely new subsystem — chain computation on
write, an integrity-verification job, and (for full parity) an external
anchoring integration — none of which is free to design, implement, or
test. This project's learning budget is fixed at exactly two slots (RAG
evaluation methodology, LLM guardrails/prompt-injection defence,
`00a-ledger-confirmation.md`), both already spent; a hash-chain-plus-
anchoring subsystem is itself a distinct pattern to learn and would need
its own budget conversation, not a quiet addition inside a threat-model
session. No document in this project's own discovery/requirements work
names a driver strong enough to justify that cost. Rejected as
disproportionate to `lexicon`'s actual, stated threat model.

### B — Application-layer append-only-by-convention only (status quo)

**For:** Zero additional cost; already true today (`04-data-model.md`'s
existing invariant: no update path exists in application code).

**Against:** "By convention" is not a control, it is the absence of one —
it does nothing against the realistic threat this ADR exists to address (a
privileged database actor bypassing the application layer entirely via
direct SQL). Reaffirming the status quo unchanged would not actually
resolve the question Session 2 left open; it would just re-defer it a
second time. Rejected.

### C — DB-level permission enforcement (chosen)

Restrict `UPDATE`/`DELETE` grants on `QUERY_LOG`, `RETRIEVED_CHUNK`, and
`CITATION_VERDICT` to the migration/admin database role only. The
application's runtime database role receives `INSERT`/`SELECT` on these
three tables and nothing else — no grant path exists for the running
application, under any application-layer bug or compromised application
credential, to modify or remove a historical audit row.

**For:** Directly closes the two realistic tamper paths for `lexicon`'s
actual deployment shape (self-hosted, single operator, no named external
evidentiary driver): (i) an application bug that accidentally mutates
history, and (ii) a compromised application-layer credential (e.g. via a
future SQL-injection-class bug, or a leaked application `.env` value)
being used to edit the trail. This is the same realistic-threat class
`privacy-forge`'s own T-16 mitigation targets (`06-security-threat-model.md`
there: "DB-level `UPDATE` grant on `policy_definitions` restricted to the
migration/seeding process, not the application's runtime role") — a
genuinely applicable, narrowly-scoped precedent, unlike full
hash-chaining. Implementation cost is a database grant statement, not a
subsystem; fully testable via a grant-assertion test.

**Against:** Does not resist a fully privileged actor holding the
migration-level/superuser database credential itself (a true insider with
root database access) — the same residual limit `privacy-forge`'s own
hash-chain-without-anchoring already accepts for equivalent-tier
compromise (see that project's Accepted Risks: "Hash-chain anchor
unavailability degrades tamper-evidence to chain-only, not full
protection"). Also provides no cryptographic proof of reordering or
deletion — an emptied table under this design is just an emptied table,
not a visibly broken chain. This limitation is named honestly, not hidden;
see Accepted Risks in `06-security-threat-model.md`.

## Decision

**Option C.** Append-only is enforced by database permission grants, not
merely by application-code convention. Hash-chaining is explicitly **not**
built for v1.

## Trade-offs accepted

- Residual risk from a fully-privileged/insider database actor (one who
  holds the migration-level credential itself, not just the application's
  runtime credential) is not eliminated by this design. Named explicitly
  in `06-security-threat-model.md`'s Accepted risks, with a revisit
  trigger, rather than left implicit.
- No cryptographic non-repudiation exists for this audit trail — it is not
  suitable as legal-evidentiary proof against a determined, fully
  privileged adversary. If `lexicon` is ever positioned for a use case that
  requires that property, this decision must be revisited before that
  positioning is made, not after.

## Consequences

- Session 4 (Implementation) must provision two distinct database roles: a
  migration/admin role (full DDL/DML, used only by the Alembic migration
  process) and a restricted application runtime role (`INSERT`/`SELECT`
  only on `QUERY_LOG`, `RETRIEVED_CHUNK`, `CITATION_VERDICT`; ordinary
  read/write access elsewhere as needed by the rest of the application).
  This is a real interface requirement for Session 4, not a suggestion.
- `08-deployment-and-operations.md` (not yet written) must document how the
  two roles/credentials are provisioned and kept separate in a real
  deployment (e.g. distinct `DATABASE_URL`-equivalent values for the
  migration step versus the running application container).
- A grant-assertion test — confirming the application's runtime role
  genuinely lacks `UPDATE`/`DELETE` on the three audit tables, executed
  against a real database connection using that role, not a config review —
  is a Session 4 requirement, referenced as T-07's verification in
  `06-security-threat-model.md`.

## Revisit triggers

- If `lexicon` is ever deployed for an operator with a real external
  evidentiary requirement (an enterprise or compliance customer needing to
  prove, in a dispute, that a specific `CITATION_VERDICT` was not altered
  after the fact — the same class of driver that produced `privacy-forge`'s
  ADR-0003), adopt a hash-chain design, scoped to what that requirement
  actually demands, as its own scoped decision at that time — not
  preemptively built now against a threat that isn't real yet.
- If the Session 5 evaluation harness, a real incident, or any future audit
  ever surfaces an actual case of undetected audit-trail tampering under
  this design, that is a forcing function to revisit this ADR immediately,
  not on the next scheduled session.
