# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `install.sh --upgrade --adopt FILE`: mark a kit payload path adopter-owned — the kit never writes, merges, or re-adds it.
- `--upgrade` never replaces or deletes an installed CI workflow; template changes are reported. The new CI template fails until a project sets its check command, so existing pipelines keep running.
- `--upgrade` deletes files the kit no longer ships when the adopter never edited them, and directories that leaves empty. Edited, adopted, and untracked files stay and are reported.

### Changed

- **Breaking: workflow redesign.** Seven stages instead of nine (Foundation, Plan, Decompose, Build, Review, Land, Retro) with three hard gates plus a conditional one at Build. `AGENTS.md` now carries the gates and seven no-compromise rules on its own, so any harness that reads it runs the workflow.
- Living specs (`docs/specs/`) state current behavior with requirement IDs that tests cite; change proposals (`docs/changes/`) replace feature PRDs, amendment PRDs, and briefs.
- Artifacts have line budgets. ADRs fit one screen; security records are a findings-and-resolutions table; `docs/security.md` is a trust-boundary table.
- Sensitive now means a change to a trust boundary, and review findings are weighed against the project's Lifecycle: hardening for absent traffic goes to the production register.
- Stage 0 proves each part of the check command fails on its own planted error, one per run, and records CI as unproven until the first push. A new project documents only what exists.
- `docs/test-strategy.md` sets test layers by where bugs surface, plus parallel-safe tests, affected-only pull request runs, and a full run on the default branch.
- `code-review` absorbs `code-simplification` and `definition-of-done-review`; the conductor holds all stage procedure in one file.
- `code-review` and `security-review` are rewritten as kit-owned skills and no longer carry upstream notices.
- The PR template adds a "Where to look" section and a criterion-to-test proof table. The CI template is stack-neutral and fails until the project sets its check command.
- Lifecycle records team shape: solo projects land the proposal with the first task's PR; team projects land it on `main` first.
- Projects without an external tracker keep tasks in the change proposal instead of `docs/progress.md`.

### Removed

- Skills: `brainstorming`, `to-spec`, `documentation-and-adrs`, `writing-plans`, `feature-start`, `project-status`, `ponytail`, `webapp-testing`, `code-simplification`, `definition-of-done-review`.
- Templates: `docs/prd/`, `docs/briefs/`, `docs/progress.md`, `docs/adr/0001-record-architecture-decisions.md`.
- Hash-bound review identities, per-check private worktrees, and the per-file security coverage ledger.

Upgrading: `--upgrade` deletes the removed skills and untouched templates. Filled PRDs, briefs, and `docs/progress.md` stay; fold them into `docs/specs/` and change proposals at the next Stage 0 adoption pass. If a removed skill directory remains (`!` lines), you edited it: delete it so agents do not load stale nine-stage instructions.

- Landings verify the named artifacts were committed; reviewers get raw artifacts, not implementer narratives.

## [0.1.0] - 2026-10-03

Initial release.
