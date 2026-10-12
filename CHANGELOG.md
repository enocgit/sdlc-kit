# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `install.sh --upgrade --adopt FILE`: mark a kit payload path adopter-owned — the kit never writes, merges, or re-adds it.
- `install.sh --upgrade --resolved FILE`: after a hand merge, keep the file, re-anchor it on the current kit version, end any adoption, and remove its conflict file, so later upgrades merge instead of conflicting again.
- `--upgrade` removes `.sdlc-vendor/` metadata that older installers left in skill directories, and directories that leaves empty.
- `--upgrade` never replaces or deletes an installed CI workflow; template changes are reported. The new CI template fails until a project sets its check command, so existing pipelines keep running.
- `--upgrade` deletes files the kit no longer ships when the adopter never edited them, and directories that leaves empty. Edited, adopted, and untracked files stay and are reported.
- `--upgrade` ignores kit rewordings of placeholder lines, so a filled placeholder no longer turns every other change in the file into a conflict. A conflict report names how many regions need resolving; the `.sdlc-conflict` file already holds every other kit change.

### Changed

- **Breaking: workflow redesign.** The nine stages and the `sdlc` conductor skill are gone. `AGENTS.md` carries the seven no-compromise rules, two gates (approve plan; a maintainer merges), how a change moves from plan to merge, and the review order, so any harness that reads it runs the workflow. Bug fixes and chores skip planning. `bootstrap` sets a project up once.
- Review runs before the PR in a context that did not write the change, first available: a subagent or headless agent CLI on a different model, then either on the same model. `AGENTS.md` is the instruction to delegate it, so harnesses that refuse unrequested subagents still run it. The reviewer gets raw artifacts, judges sensitivity itself, and re-reviews the new diff; a maintainer is asked about the design after a third blocked round; the PR names the reviewer, its model, and the verdict. A review bot adds to this review and never replaces it.
- `code-review` confirms library behavior in the installed source, and treats a missing artifact as a note for the PR rather than a block, except for the smoke check.
- Change proposals carry a smoke check on realistic input: what its user must get from it, approved with the plan, whose gate message quotes it. It is a look at the running product, not a test. The slice that completes the behavior runs it where `docs/test-strategy.md` → Local run says and uses the output as its user would; a maintainer runs what Local run does not cover, from steps in the PR. The reviewer judges the raw output, and a miss is a required finding. A check that cannot run as approved is explained in the PR and left to whoever merges. Test data must carry the variation real inputs have.
- Every task that changes files ends on its own branch, reviewed, with a PR open, without asking first.
- `docs/test-strategy.md` gains Local run: the command that starts the app or a UI harness without production secrets, and what a maintainer checks elsewhere. `bootstrap` proves it starts. UI checks and smoke checks run there.
- Every added or changed requirement in a change proposal has at least one acceptance criterion with its test layer.
- A change too big for one review lists its slices in the proposal; with a tracker, plan approval covers creating one issue per slice. Each slice gets its own branch and PR. Projects without a tracker keep slices in the proposal instead of `docs/progress.md`.
- Living specs (`docs/specs/`) state current behavior with requirement IDs that tests cite; change proposals (`docs/changes/`) replace feature PRDs, amendment PRDs, and briefs.
- **Breaking:** `docs/security.md` is now `docs/threat-model.md`: a trust-boundary table plus the index of security records in `docs/security/records/`. Security records are a findings-and-resolutions table; ADRs fit one screen.
- Sensitive means a change to a trust boundary, including any boundary listed in the project's `docs/threat-model.md`, and review findings are weighed against the project's Lifecycle: hardening for absent traffic goes to the production register.
- `bootstrap` proves each part of the check command fails on its own planted error, one per run, and the first CI run's log confirms each part ran. The check covers all code, tests included: existing failures are fixed or reported, never excluded. It ends with two exact scans for leftover placeholders and workflow terms, and nothing lands before the foundation is approved. Adopting an existing codebase changes its CI to run the check.
- `templates/AGENTS.md` fits in 125 lines, leaving 25 of the 150-line budget for project facts. Adopters keep its lines as written so upgrades merge, and put project facts in the project sections.
- Requirement IDs live in specs, proposals, and test names; code comments no longer repeat them.
- `docs/test-strategy.md` sets test layers by where bugs surface, plus parallel-safe tests, affected-only pull request runs, and a full run on the default branch.
- `code-review` absorbs `code-simplification` and `definition-of-done-review`. `code-review` and `security-review` are rewritten as kit-owned skills and no longer carry upstream notices.
- The PR template adds a "Where to look" section and a criterion-to-test proof table. The CI template is stack-neutral and fails until the project sets its check command.
- Lifecycle records team shape: solo projects land the proposal with the first slice's PR; team projects land it on `main` first.
- `required-skills.yml` records where `AGENTS.md` uses each skill (`use: setup | plan | build | review`) instead of a stage number.

### Removed

- Skills: `sdlc` (the conductor), `diagnosing-bugs`, `improve-codebase-architecture`, `brainstorming`, `to-spec`, `documentation-and-adrs`, `writing-plans`, `feature-start`, `project-status`, `ponytail`, `webapp-testing`, `code-simplification`, `definition-of-done-review`.
- Templates: `docs/contracts/README.md` (create the index when the first contract is frozen), the epic issue template, `docs/prd/`, `docs/briefs/`, `docs/progress.md`, `docs/adr/0001-record-architecture-decisions.md`.
- Stage banners, the decompose and retro stages, gate-message formats outside bootstrap, artifact line budgets, and parallel task groups.
- Hash-bound review identities, per-check private worktrees, and the per-file security coverage ledger.
- `CHEATSHEET.md`: `AGENTS.md` is the summary.

Upgrading:

1. Rename first: `git mv docs/security.md docs/threat-model.md`, and update links to it. Without this, the upgrade adds an empty `docs/threat-model.md` beside your filled `docs/security.md`. After the rename, the upgrade reports `docs/threat-model.md` as kept and untracked; that is expected.
2. Run `--upgrade`. It deletes the removed skills and untouched templates. A filled `docs/contracts/README.md`, PRDs, briefs, or `docs/progress.md` stay; fold the last three into `docs/specs/` and change proposals. If a removed skill directory remains (`!` lines), you edited it: delete it so agents do not load stale stage instructions.
3. Resolve the `AGENTS.md` conflict, usually one region in Conventions where your filled lines meet changed kit lines, then mark it with `--resolved AGENTS.md`.
4. Fill Local run in `docs/test-strategy.md`: start the command once, and list what it cannot reach under Not covered.

## [0.1.0] - 2026-10-03

Initial release.
