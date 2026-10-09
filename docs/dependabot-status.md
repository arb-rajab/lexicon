# Dependabot status

_Last updated: 2026-10-09. Maintained during the Dependabot clean-up pass; update when the state changes._

## Configuration

- Ecosystems covered: pip (`/backend`, `/docs/spikes/session1-hybrid-retrieval`), npm (`/frontend`), docker (`/backend`, `/frontend`), github-actions (`/`), docker-compose (`/`).
- Grouping: `minor-and-patch` for every ecosystem (open-PR limit 5 each).
- Schedule: weekly.
- Ignore rules: `typescript` majors (typescript-eslint does not load on TS 7); `eslint` majors (eslint-config-next peers eslint <= 9); `eslint-config-next` majors (16 is flat-config only and enables react-hooks v7 rules that flag existing components); docker-compose image majors (stateful services need a deliberate migration).

## State at last update

- Open Dependabot PRs: 0 (each merged or closed only after reading its checks).
- Default-branch CI: green at last check.
- Last full rescan: 2026-10-09. Checked open PRs (none), default-branch and scheduled CI, Dependabot update jobs, ecosystem coverage (no new manifests since 2026-10-08), Actions pins, exemption expiry dates and stray branches, plus three new dimensions: branch-protection required contexts against the check runs a PR actually produces, the repo's `security_and_analysis` settings, and check-run annotations on `main`. No required context is stale. The annotations showed `ubuntu-latest` moving to Ubuntu 26 from 2026-10-19, so every job is now pinned to `ubuntu-24.04` (see Notes). The full-history gitleaks scan was not repeated: the only commits since 2026-10-08 are docs and CI changes, each scanned by the push-run gitleaks job. Rescan cycle 2 (same day, after those pins merged) repeated every dimension and added one: each repo's `SECURITY.md` and whether GitHub private vulnerability reporting is enabled.

## Time-limited exemptions

- `osv-scanner.toml` (approved by the repo owner 2026-10-08, merged in #30): dev-only `braces` 3.0.3 (GHSA-vfj7-8cjw-p6xm, no patched release), `ignoreUntil` 2026-11-15.

## Notes

- `docker/Dockerfile.prod` directories are not covered by a `docker` entry; this is a known, deliberately deferred gap.
- The CI `npm audit --omit=dev` step skips dev dependencies, so an `osv-scanner` job (`dependency-scan` in `ci.yml`) now gates the whole frontend lockfile. Background: a manual OSV query of `frontend/package-lock.json` (2026-10-08) found `brace-expansion` 1.1.18 / 5.0.9 (dev-only, three advisories, two HIGH: GHSA-6j4f-fj2g-mc7p, GHSA-qhr7-859c-m2p7, plus GHSA-q2hr-2g5m-vwhr); the lockfile now has 1.1.21 / 5.0.12. The only remaining finding is dev-only `braces` 3.0.3 (GHSA-vfj7-8cjw-p6xm), which has no patched release.

- The `dependency-scan` job deliberately scans only `frontend/package-lock.json`. `docs/spikes/session1-hybrid-retrieval/requirements.txt` (an experiment, not deployed, no lockfile) was tried and left out: osv-scanner resolves its transitive tree and reports `anyio` 4.9.0 (PYSEC-2026-4024/4025, up to CVSS 9.3, fixed in 4.14.2) and `idna` 3.9.0 (PYSEC-2026-215, fixed in 3.15) via `fastembed`. The spike's `pip` Dependabot entry still covers it; add it to the scan once it has a lockfile or constraints.
- `.gitleaksignore` (added 2026-10-08): one fingerprint, the public jwt.io sample token in `docs/spikes/session1-hybrid-retrieval/corpus/oauth2-jwt.md` (commit ce4b4739). CI's gitleaks job only scans new commits, so it never failed; a full-history scan did.
- Every workflow declares a top-level `permissions: contents: read` (added 2026-10-08, rescan cycle 3). Jobs that need more, such as CodeQL's `security-events: write`, declare it at job level.
- Merge policy (deliberate choice by the repo owner, 2026-10-08): every PR, major-version dependency bumps included, is merged as soon as all of its required checks are green, confirmed per PR. This repo is a code showcase with no business or sensitive dependency, so green checks are the only gate. Red, pending or conflicted PRs are fixed or closed instead.
- Every Linux job runs on `ubuntu-24.04` (pinned 2026-10-09; it is what `ubuntu-latest` resolved to). GitHub moves `ubuntu-latest` to Ubuntu 26 from 2026-10-19, and an unattended image change could turn every check red at once. Move to `ubuntu-26.04` deliberately, in one PR whose CI has run on it. Dependabot does not bump `runs-on` labels.
- `Dependency vulnerability scan (osv-scanner)` is a required check since 2026-10-09. It ran on every PR but was not required (found in that day's rescan), so under the merge policy a red scan would not have blocked a merge. Added by the repo owner through the API; the required-contexts list read before and after differs only by this entry.
- `SECURITY.md` sends reporters to GitHub private vulnerability reporting. It was disabled here (found 2026-10-09, rescan cycle 2); the repo owner changed it through the API on 2026-10-09 and the read-back confirmed it (`enabled: true`).

## Deferred (not re-raised each pass)

- Ignored major versions are listed in `.github/dependabot.yml` with the reason for each.
- Re-check exemptions before their `effectiveUntil` date (2026-11-15) and drop them once upstream fixes ship.
- Alerts read 2026-10-09 with the repo owner's PAT, run on their machine (Claude sessions still get 403: the proxy sends a GitHub App token instead of `GH_ALERTS_TOKEN`, even a PAT passed explicitly). No open Dependabot or code-scanning alerts. Re-read 2026-10-09 after rescan cycle 2: still no open alerts.
