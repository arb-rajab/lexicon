"""ADR-0005 — real instance-level authentication primitives (password
hashing, session-token issuance/verification). Kept separate from
`lexicon.api` because these are pure security primitives with no FastAPI
dependency injection concerns of their own — `lexicon.api.auth` is what
wires them into the request pipeline.
"""
