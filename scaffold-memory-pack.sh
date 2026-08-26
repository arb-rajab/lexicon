#!/usr/bin/env bash
# scaffold-memory-pack.sh
# Creates the Project Memory Pack + SDLC evidence map in the current repository.
# Usage: ./scaffold-memory-pack.sh "project-name" "public|private"
set -euo pipefail

NAME="${1:-unnamed-project}"
TRACK="${2:-public}"
DATE="$(date +%Y-%m-%d)"
DIR="docs/project-memory"

mkdir -p "$DIR" docs/adr docs/architecture

hdr() { printf '# %s\n> Purpose: %s\n> Project: %s (%s)\n> Last updated: %s\n\n' "$1" "$2" "$NAME" "$TRACK" "$DATE"; }

[ -f "$DIR/00-project-brief.md" ] || {
hdr "Project Brief" "single source of truth for what this project is and why it exists" > "$DIR/00-project-brief.md"
cat >> "$DIR/00-project-brief.md" <<'EOF'
## One-line description
## Problem statement
## Target users and stakeholders
## Business assumptions
## Why this project exists in the portfolio
- Technology/learning objective:
- SDLC phases demonstrated deeply:
## Success metrics
## Feasibility notes and key risks
## Elevator pitch
EOF
}

[ -f "$DIR/01-scope-and-non-goals.md" ] || {
hdr "Scope and Non-Goals" "prevent scope creep by writing down what this will never do" > "$DIR/01-scope-and-non-goals.md"
cat >> "$DIR/01-scope-and-non-goals.md" <<'EOF'
## MVP boundary (in scope)
## Explicit non-goals
| Non-goal | Why excluded | Would reconsider if |
|---|---|---|
## Deferred to backlog
## Definition of "v1 complete"
EOF
}

[ -f "$DIR/02-requirements.md" ] || {
hdr "Requirements" "testable statements of what the system must do and how well" > "$DIR/02-requirements.md"
cat >> "$DIR/02-requirements.md" <<'EOF'
## Roles and permissions matrix
| Role | Can | Cannot |
|---|---|---|
## User stories with acceptance criteria
## Functional requirements
| ID | Requirement | Priority | Verified by |
|---|---|---|---|
## Non-functional requirements (numeric targets only)
| ID | Category | Requirement | Target | Verified by |
|---|---|---|---|---|
## Data classification
| Data element | Classification | Retention | Encryption | Lawful basis |
|---|---|---|---|---|
## Integration requirements
## Constraints
EOF
}

[ -f "$DIR/03-architecture.md" ] || {
hdr "Architecture" "how the system is structured and why" > "$DIR/03-architecture.md"
cat >> "$DIR/03-architecture.md" <<'EOF'
## System context diagram
```mermaid
C4Context
```
## Container/component diagram
## Component responsibilities and boundaries
## Key flows
## Scalability approach
## Failure handling and degradation modes
## Backup and recovery design (RPO / RTO)
## Technology choices (links to ADRs)
EOF
}

[ -f "$DIR/04-data-model.md" ] || {
hdr "Data Model" "the authoritative description of stored data" > "$DIR/04-data-model.md"
cat >> "$DIR/04-data-model.md" <<'EOF'
## ERD
```mermaid
erDiagram
```
## Entity descriptions
| Entity | Purpose | Key attributes | Classification |
|---|---|---|---|
## Invariants and where they are enforced
## Indexing strategy
## Migration approach and rollback
## Retention and deletion rules
EOF
}

[ -f "$DIR/05-api-contracts.md" ] || {
hdr "API / Event Contracts" "the interface others depend on" > "$DIR/05-api-contracts.md"
cat >> "$DIR/05-api-contracts.md" <<'EOF'
## Style and rationale
## Authentication and authorisation model
## Endpoints / schema summary
## Error model
## Versioning and deprecation policy
## Idempotency, pagination, rate limits
## Events published/consumed
EOF
}

[ -f "$DIR/06-security-threat-model.md" ] || {
hdr "Security and Threat Model" "what can go wrong, and what stops it" > "$DIR/06-security-threat-model.md"
cat >> "$DIR/06-security-threat-model.md" <<'EOF'
## Assets and data classification
## Trust boundaries
## Threats (STRIDE)
| ID | Boundary | Threat | Category | L/I | Mitigation | Verified by |
|---|---|---|---|---|---|---|
## Abuse cases
## Authentication and authorisation design
## Secrets management
## Dependency and supply-chain controls
## Accepted risks (reason + revisit trigger)
EOF
}

[ -f "$DIR/07-testing-strategy.md" ] || {
hdr "Testing Strategy" "what we test, at which level, and why that is sufficient" > "$DIR/07-testing-strategy.md"
cat >> "$DIR/07-testing-strategy.md" <<'EOF'
## Testing philosophy for this project
## Levels
| Level | Tool | Scope | Gate |
|---|---|---|---|
## Security testing
## Accessibility testing
## Performance testing and budgets
## Test data strategy (synthetic only)
## Quality gates in CI
## Known gaps and why they are acceptable
EOF
}

[ -f "$DIR/08-deployment-and-operations.md" ] || {
hdr "Deployment and Operations" "how this runs, and how someone else keeps it running" > "$DIR/08-deployment-and-operations.md"
cat >> "$DIR/08-deployment-and-operations.md" <<'EOF'
## Environments
## Build and release pipeline
## Deployment procedure
## Migration and rollback procedure
## Configuration and secrets
## Observability: logs, metrics, traces, health checks
## Dashboards and alerts (each links a runbook)
## Runbooks
## Backup and restore (last verified: NEVER — update this)
## Capacity and cost notes
EOF
}

[ -f "$DIR/09-decision-log.md" ] || {
hdr "Decision Log" "why things are the way they are, so decisions are not silently undone" > "$DIR/09-decision-log.md"
cat >> "$DIR/09-decision-log.md" <<'EOF'
## ADR-0001 — <title>
- **Date:**
- **Status:** proposed
- **Context:**
- **Options considered:**
- **Decision:**
- **Trade-offs accepted:**
- **Consequences:**
- **Revisit triggers:**
EOF
}

[ -f "$DIR/10-risk-register.md" ] || {
hdr "Risk Register" "known risks, owned and reviewed rather than forgotten" > "$DIR/10-risk-register.md"
cat >> "$DIR/10-risk-register.md" <<'EOF'
| ID | Risk | Category | Impact | Likelihood | Mitigation | Status | Review date |
|---|---|---|---|---|---|---|---|
## Closed risks
EOF
}

[ -f "$DIR/11-backlog.md" ] || {
hdr "Backlog" "everything deliberately not being done right now" > "$DIR/11-backlog.md"
cat >> "$DIR/11-backlog.md" <<'EOF'
## Next up
| ID | Item | Type | Size | Why now |
|---|---|---|---|---|
## Later
## Explicitly rejected (with reasons)
EOF
}

[ -f "$DIR/12-session-handoff.md" ] || {
cat > "$DIR/12-session-handoff.md" <<'EOF'
# Session Handoff

## Project
- Repository:
- Public or private:
- Product/domain:
- Current version or branch:

## Session completed
- Session number and title: Session 0 — Governance and setup
- Objective:
- Status: complete / partially complete / blocked

## Work completed

## Files created or changed

## Decisions made

## Validation performed
- Commands run:
- Tests run and results:
- Lint / static analysis / security scan results:
- Manual checks performed:

## Open questions and risks

## Next recommended session
- Proposed session title:
- Single objective:
- Inputs required:
- Expected deliverables:
- Definition of done:

## Paste-into-new-session context
<!-- Self-contained block. NEVER include credentials, private URLs, customer
     data, proprietary business rules, or sensitive security details. -->
EOF
}

[ -f "$DIR/13-release-notes.md" ] || {
hdr "Release Notes" "what changed, for humans" > "$DIR/13-release-notes.md"
cat >> "$DIR/13-release-notes.md" <<'EOF'
## Unreleased
### Added
### Changed
### Fixed
### Security
### Migration notes
### Rollback instructions
EOF
}

[ -f "$DIR/14-maintenance-and-retirement.md" ] || {
hdr "Maintenance and Retirement" "the whole life of the system, including its end" > "$DIR/14-maintenance-and-retirement.md"
cat >> "$DIR/14-maintenance-and-retirement.md" <<'EOF'
## Maintenance cadence
- Dependency updates:
- Security patching SLA:
- Backup restore test:
## Support model and expectations
## Data export and portability
## Data retention and deletion schedule
## Handover pack
## Decommissioning procedure
## End-of-life policy
## Dependency support horizons
EOF
}

[ -f "docs/SDLC-EVIDENCE.md" ] || {
cat > docs/SDLC-EVIDENCE.md <<'EOF'
# SDLC Evidence Map

**Deep phases:**
**Baseline phases:**
**Intentionally light:** — because

| Phase | Depth | Evidence | Location |
|---|---|---|---|
| 1. Discovery & Planning | | | |
| 2. Requirements Analysis | | | |
| 3. Architecture & Design | | | |
| 4. Implementation | | | |
| 5. Verification & Testing | | | |
| 6. Release & Deployment | | | |
| 7. Operations & Maintenance | | | |
| 8. Retirement & Handover | | | |

## Why some phases are light
EOF
}

echo "Project Memory Pack scaffolded for '$NAME' ($TRACK) in $DIR"
echo "Next: complete 00-project-brief.md in Session 1, then commit:"
echo "  git add docs && git commit -m 'docs(S0): scaffold project memory pack'"
