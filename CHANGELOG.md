# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `install.sh --upgrade --adopt FILE`: mark a kit payload path adopter-owned — the kit never writes, merges, or re-adds it.
- `--upgrade` never replaces or deletes an installed CI workflow; template changes are reported. The new CI template fails until a project sets its check command, so existing pipelines keep running.
- `--upgrade` deletes files the kit no longer ships when the adopter never edited them, and directories that leaves empty. Edited, adopted, and untracked files stay and are reported.
- `--upgrade` ignores kit rewordings of placeholder lines, so a filled placeholder no longer turns every other change in the file into a conflict. A conflict report names how many regions need resolving; the `.sdlc-conflict` file already holds every other kit change.

### Changed

- **Breaking: workflow redesign.** Seven stages instead of nine (Foundation, Plan, Decompose, Build, Review, Land, Retro) with three hard gates plus a conditional one at Build. `AGENTS.md` now carries the gates and seven no-compromise rules on its own, so any harness that reads it runs the workflow.
- Every added or changed requirement in a change proposal has at least one acceptance criterion with its test layer.
- `AGENTS.md` tells agents to load the `sdlc` skill before any product change, bug fixes included; a bug fix states the report's input and the expected result as its real-world check, and asks when the report is ambiguous.
- Change proposals carry a real-world check: a realistic input and what its user must get from it, agreed in planning. The task that completes the behavior runs it and uses the output as its user would; the reviewer judges that raw output, and a miss is a required finding. Test data must carry the variation real inputs have.
- Living specs (`docs/specs/`) state current behavior with requirement IDs that tests cite; change proposals (`docs/changes/`) replace feature PRDs, amendment PRDs, and briefs.
- Artifacts have line budgets. ADRs fit one screen; security records are a findings-and-resolutions table; `docs/security.md` is a trust-boundary table.
- Sensitive now means a change to a trust boundary, including any boundary listed in the project's `docs/security.md`, and review findings are weighed against the project's Lifecycle: hardening for absent traffic goes to the production register.
- Stage 0 proves each part of the check command fails on its own planted error, one per run; Retro reads the first CI run's log to confirm each part ran. A new project documents only what exists, and review rejects workflow terms in product artifacts.
- `docs/test-strategy.md` sets test layers by where bugs surface, plus parallel-safe tests, affected-only pull request runs, and a full run on the default branch.
- `code-review` absorbs `code-simplification` and `definition-of-done-review`; the conductor holds all stage procedure in one file.
- `code-review` and `security-review` are rewritten as kit-owned skills and no longer carry upstream notices.
- The PR template adds a "Where to look" section and a criterion-to-test proof table. The CI template is stack-neutral and fails until the project sets its check command.
- Each task gets its own branch and PR; after it lands, the next task returns to Stage 3. A sensitive task's Stage 3 stop names only what it adds beyond the approved plan.
- The reviewer, not the author, judges sensitivity, and a finding or fix that changes a listed security control makes the change sensitive.
- Stage 4 names the review skills for the reviewer to load and runs `security-review` in the same fresh context as `code-review`, and re-reviews get the new diff and commits, not the author's account. The human is asked about the design after a fifth blocked round.
- With no remote, CI is reported once as not run, and Retro edits commit to the local default branch without an ask. A part added to the check command must fail on a planted error before it counts.
- Nothing lands before its gate's approval. Gate messages are three plain lines, not a list; they name anything unproven and any check skipped, and do not restate the files. Stage 0 ends with two exact scans for leftover placeholders and workflow terms.
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
