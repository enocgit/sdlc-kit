# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-07-06

Initial release.

### Added
- Plan-gated SDLC pipeline (stages 0–8) driven by the `sdlc` conductor skill, which routes each
  stage to the right skill and enforces human approval gates.
- Right-sizing / fast-path so trivial changes skip ceremony (features run the full pipeline;
  fixes and chores take a shorter path).
- Hybrid artifacts: in-repo `docs/` (context, architecture, PRD, ADR, contracts, security, test
  strategy, runbook) plus GitHub Issues/Projects as the single source of truth for live tracking
  (no in-repo mirror; `project-status` reports it read-only).
- New- and existing-project on-ramps (`bootstrap` / `adopt`).
- Custom skills: `sdlc`, `feature-start`, `project-status`, `definition-of-done-review`, and
  `address-review` (standalone, user-invoked triage of external PR review comments); community
  skills wired in via `INSTALL.md`.
- Definition of Ready + Definition of Done; CI template (`templates/ci.yml`) enforcing the
  mechanical half; threat-model touch + `security.md`; expand/contract migration discipline;
  GitHub Flow branching.
- Merge-aware `install.sh` (file-level no-clobber, `--dry-run`, conflict report; also installs
  GitHub PR/issue templates) and open-source files (`LICENSE`, `CONTRIBUTING.md`, this changelog,
  `.gitignore`).
- `required-skills.yml` (machine-readable skill manifest with per-skill source/stage/fallback)
  and `scripts/validate-kit.sh` (maintainer/CI checks: install smoke test, frontmatter,
  placeholder hygiene).
- Stage-0 "context filled" gate: the conductor detects an unfilled `docs/context.md` (STATUS
  marker / `{placeholder}` tokens) and won't advance to Spec until it's completed.
- Canonical "Sensitive areas" list in `AGENTS.md`, referenced by `security.md`, the conductor,
  and the DoD reviewer (no more drift).
- Templates: `docs/briefs/TEMPLATE.md` and `.github/` PR + issue templates aligned to
  PRD / acceptance criteria / contract / security / DoD.
