# Dependabot status

_Last updated: 2026-10-08. Maintained during the Dependabot clean-up pass; update when the state changes._

## Configuration

- Ecosystems covered: pip (`/backend`, `/docs/spikes/session1-hybrid-retrieval`), npm (`/frontend`), docker (`/backend`, `/frontend`), github-actions (`/`), docker-compose (`/`).
- Grouping: `minor-and-patch` for every ecosystem (open-PR limit 5 each).
- Schedule: weekly.
- Ignore rules: `typescript` majors (typescript-eslint does not load on TS 7); `eslint` majors (eslint-config-next peers eslint <= 9); `eslint-config-next` majors (16 is flat-config only and enables react-hooks v7 rules that flag existing components); docker-compose image majors (stateful services need a deliberate migration).

## State at last update

- Open Dependabot PRs: 0 (each merged or closed only after reading its checks).
- Default-branch CI: green at last check.

## Time-limited exemptions

- None.

## Notes

- `docker/Dockerfile.prod` directories are not covered by a `docker` entry; this is a known, deliberately deferred gap.
- No osv-scanner config in this repo.

## Deferred (not re-raised each pass)

- Ignored major versions are listed in `.github/dependabot.yml` with the reason for each.
- Re-check exemptions before their `effectiveUntil` date (2026-11-15) and drop them once upstream fixes ship.
