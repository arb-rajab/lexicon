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

- `osv-scanner.toml` (proposed, awaiting owner approval): dev-only `braces` 3.0.3 (GHSA-vfj7-8cjw-p6xm, no patched release), `ignoreUntil` 2026-11-15.

## Notes

- `docker/Dockerfile.prod` directories are not covered by a `docker` entry; this is a known, deliberately deferred gap.
- The CI `npm audit --omit=dev` step skips dev dependencies, so an `osv-scanner` job (`dependency-scan` in `ci.yml`) now gates the whole frontend lockfile. Background: a manual OSV query of `frontend/package-lock.json` (2026-10-08) found `brace-expansion` 1.1.18 / 5.0.9 (dev-only, three advisories, two HIGH: GHSA-6j4f-fj2g-mc7p, GHSA-qhr7-859c-m2p7, plus GHSA-q2hr-2g5m-vwhr); the lockfile now has 1.1.21 / 5.0.12. The only remaining finding is dev-only `braces` 3.0.3 (GHSA-vfj7-8cjw-p6xm), which has no patched release.

- The `dependency-scan` job deliberately scans only `frontend/package-lock.json`. `docs/spikes/session1-hybrid-retrieval/requirements.txt` (an experiment, not deployed, no lockfile) was tried and left out: osv-scanner resolves its transitive tree and reports `anyio` 4.9.0 (PYSEC-2026-4024/4025, up to CVSS 9.3, fixed in 4.14.2) and `idna` 3.9.0 (PYSEC-2026-215, fixed in 3.15) via `fastembed`. The spike's `pip` Dependabot entry still covers it; add it to the scan once it has a lockfile or constraints.

## Deferred (not re-raised each pass)

- Ignored major versions are listed in `.github/dependabot.yml` with the reason for each.
- Re-check exemptions before their `effectiveUntil` date (2026-11-15) and drop them once upstream fixes ship.
