# Corpus provenance and licence

Source: [tiangolo/fastapi](https://github.com/tiangolo/fastapi), `docs/en/docs/` tree,
fetched 2026-08-27 from `raw.githubusercontent.com` at the `master` ref.

Licence: FastAPI (code and documentation) is MIT-licensed. Redistribution as a
fixed snapshot for a non-commercial, internal feasibility spike — with
attribution and the original source recorded here — is within the terms of
that licence. This corpus is not redistributed as part of any shipped
product; it exists only inside this spike directory for a one-time retrieval
experiment.

## Why this corpus

`lexicon` targets grounded Q&A over a specific, bounded document set with
citable facts (see `docs/project-memory/00-project-brief.md`). Official
technical documentation is a realistic stand-in for that use case: it is
fact-dense, has a real information architecture (headings, cross-references),
and — critically — it is a domain where a fabricated-but-plausible answer is
easy to produce and easy to get subtly wrong (e.g. inventing a parameter name
that sounds right). That is exactly the failure mode this project exists to
prevent, which makes it a fair test corpus rather than a toy one.

Fiction or Wikipedia trivia was deliberately avoided: neither has the
"specific, narrow, fact-checkable API/config surface" shape that the actual
target use case (internal engineering/policy/product documentation) has.

## Files

| File | Source URL |
|---|---|
| `dependencies.md` | `docs/en/docs/tutorial/dependencies/index.md` |
| `background-tasks.md` | `docs/en/docs/tutorial/background-tasks.md` |
| `sql-databases.md` | `docs/en/docs/tutorial/sql-databases.md` |
| `websockets.md` | `docs/en/docs/advanced/websockets.md` |
| `oauth2-jwt.md` | `docs/en/docs/tutorial/security/oauth2-jwt.md` |
| `docker.md` | `docs/en/docs/deployment/docker.md` |
| `cors.md` | `docs/en/docs/tutorial/cors.md` |
| `middleware.md` | `docs/en/docs/tutorial/middleware.md` |
