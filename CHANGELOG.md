# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); this project aims to follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Stage 8 (Retro) closes every retro with a concrete line surfacing the optional `improve`
  companion — scoped to what the epic touched, or `improve next` — plus the next-feature command,
  so it no longer depends on the human remembering the skill exists. Disclosure, not a gate.
- `AGENTS.md` principle **"Don't pre-build back-compat"**: expand/contract, API versioning, and
  backfills protect a real consumer or real data already depending on the current shape, not a
  hypothetical one — ask if unsure rather than defaulting either way.

### Fixed
- **Planning gates ask for commit approval.** The gate script asked only to proceed while the
  guardrail forbids commits unless asked, so approved Stage 0–2 artifacts stayed uncommitted and
  `feature-start`'s clean-tree check stalled Stage 4. Decompose is excluded and never stops — it's
  proceed-with-disclosure; where it writes `docs/progress.md` (local-only), it discloses the
  uncommitted file and `feature-start` clears it at the Stage 4 gate, where stopping belongs.
- **Expand/contract is conditional, and the condition covers writers.** Required once a table holds
  real data or *any deployed process reads or writes it* — a deployed writer breaks on a
  renamed/dropped column or a new required one just as a reader does. It was unconditional, which
  contradicts the new back-compat principle on greenfield schema.
- **Stage 7 no longer reports the issue as closed.** The PR carries `Closes #N`, the issue stays
  open, and it closes on merge — the human's action after the gate. The Definition of Done matches;
  it asked for a "status / closed" update that default GitHub Issues cannot satisfy. On a tracker
  with no Git merge integration, close the task **after** the human confirms the merge, never at
  Land, where an abandoned or rejected PR would leave it falsely complete.
- **Closing keywords are GitHub-only.** Linear/Jira use their own keys (`ENG-123`) and a local-only
  id is a `docs/progress.md` row, so `Closes #3` either fails to close the real task or closes an
  unrelated repository issue #3. Only GitHub-backed PRs and commits carry `Closes #N`; every other
  mode moves the task to *in review* and completes it after the merge. `INSTALL.md`'s tracker-port
  guidance matches — its explicit close moved from Land to the post-merge step — and the PR
  template tells every non-GitHub mode to delete its `Closes #` line.
- **The tracker-completion rule is stated once.** `skills/sdlc/SKILL.md` gains a canonical
  **Task completion by tracker** section; the Stage 7 rows in `AGENTS.md`, `README.md`, and the
  conductor carry the GitHub default and point at it instead of each restating all three modes.
  `CHEATSHEET.md` deliberately stays self-contained — it exists to answer without a second lookup.
- **`validate-kit.sh` now guards that rule.** Check `[8]` fails if any Stage 7 row mentions
  `Closes #` without scoping it to GitHub, and if the canonical section goes missing — the drift
  that repeatedly reintroduced tracker-agnostic closing guidance.
- **Local-only and no-remote projects can complete a run.** `project-status` reads
  `docs/progress.md` instead of stopping on an unauthenticated `gh`; Decompose and Land have
  defined non-GitHub paths. Tracker mode and remote are independent — local-only replaces an
  external tracker but does not imply there is no remote — and a remote does not imply a PR
  workflow, since a bare, self-hosted, or backup remote has no PRs, branch protection, or checks.
  The decision now follows independent capabilities: with PR support, open a PR; with CI but no PR
  support, push to run CI before the human merges directly; with neither, push only if a remote
  exists and the human merges directly. A configured PR or CI workflow that is unreachable
  (expired auth, network) is a blocker to surface, never a mode. Installation now requires
  non-interactive `git push` only for projects that actually have a remote.
- **Tracker transitions are explicit, approved writes.** Stage 7's move to *in review* is a
  separate action, not a side effect of opening the PR: against an external tracker
  `project-status` is read-only, so a Linear/Jira transition needs outward-facing confirmation;
  in local-only it maintains `docs/progress.md` — its one documented write — under normal commit
  approval. Where neither has happened the tracker is reported stale, not described as moved.
- **PR and CI availability are evaluated separately.** A push-triggered CI workflow still runs when
  no PR workflow exists, and CI is N/A only when no CI workflow exists. An unreachable configured
  workflow blocks rather than becoming an exemption.
- **`feature-start` takes a task identifier, not strictly a GitHub issue number.** It accepts the
  issue number (default), a tracker key (`ENG-123`), or the `#` column of the `docs/progress.md`
  task table, and branches `feat/{id}-{slug}`; Decompose numbers those rows so the identifier
  exists. Local-only runs previously had to invent one to reach Stage 4.
- **The freshness guard no longer fails without an upstream, or branches from a stale base.** It
  pulls when there's an upstream; without one it resolves the authoritative remote first — asking
  when several exist rather than fast-forwarding off a fork — then fetches and fast-forwards onto
  its default branch. Only a repo with no remote at all is latest by definition; an unreachable
  remote falls back to its cached remote-tracking ref, and discloses when freshness is unverifiable.
- **Local-only tasks reach `Done`.** Nothing marked the merged task complete, so
  `docs/progress.md` — the authoritative tracker in that mode — went stale unless the row was
  falsely set to done before merging. A new post-merge step closes the loop before Retro: GitHub
  closes itself via `Closes #N`, an alternate tracker without Git integration is closed explicitly,
  and the local-only row moves to `Done` — after checking out and syncing the default branch, since
  the checkout is otherwise still on the just-merged `feat/*` and the update would strand there
  while `main` read *In review* permanently (PR-protected `main` lands it via a `plan/*` branch).

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
