# AGENTS.md — Operating manual for AI agents on this project
>
> Canonical agent instructions. `CLAUDE.md`, `.cursorrules`, and similar files point here.
> **Keep it lean**: target ≤150 lines. Single-source: point to the doc or skill, don't restate it.

## What this project is

<!-- One paragraph: product, users, current phase. -->
See [`docs/context.md`](./docs/context.md) for domain, glossary, personas, and hard constraints.

## Two altitudes: foundation vs feature

- **Foundation (project-level)** — the few cross-cutting decisions set once at **Stage 0**: product PRD, foundational ADRs, architecture and security skeleton, core contract. Keep it minimal.
- **Feature-level** (Stages 1–8) — brief, PRD, ADRs, and contract slice, designed as you build.

## How we work: the plan-gated pipeline

The conductor (`sdlc`) routes each stage and owns the stage table, skills, and per-stage outputs. Stop
at every gate (✅) for explicit human approval; at non-gate stages do the work, disclose decisions
worth overriding, then continue.

- **Stages:** 0 Context + Foundation · 1 Spec · 2 Architecture + Contract · 3 Decompose · 4 Implement · 5 QA · 6 Review · 7 Land · 8 Retro
- **Gates (✅):** context filled, foundation, PRD, approach + freeze, per-task plan, human merge. Decompose, QA, and Review are proceed-with-disclosure.
- **Fast paths:** bug fix → 4→5→6→7→8; chore → 4→6→7→8. Stage 0 runs once, then features run 1→8. A contract change, a sensitive area, or a new decision takes the full feature path.

Open every pipeline response with `SDLC ▸ Stage {N}/8 {Name} · {next gate or action}`.

## Where things live

- **Product PRD** (project-level vision/scope, set at Stage 0) → `docs/prd/0000-product.md`
- **Feature PRDs** → `docs/prd/NNNN-{slug}.md` (numbered from 0001, status-tracked)
- **Briefs** (optional pre-PRD note for a fuzzy idea) → `docs/briefs/NNNN-{slug}.md`
- **ADRs** (decision history; edit Proposed or Accepted ADRs only while unimplemented and dependency-free; supersede implemented or depended-on decisions) → `docs/adr/NNNN-{slug}.md`
- **Architecture** (current system shape, living) → `docs/architecture.md`
- **Contracts** (the integration source of truth) → in the codebase (`api/openapi.yaml`, tRPC routers, `schema.prisma`, Zod schemas). See `docs/contracts/README.md`.
- **Task status** → your tracker, reported live by `project-status`. _Local-only:_ `docs/progress.md` **is** the tracker
- **Test strategy, verification policy, and Definition of Ready/Done** → `docs/test-strategy.md` and this file

## Documentation writing standard

Write docs, issues, and PRs for contributor decisions and verification, not narrative: lead with
status, scope, outcome, rationale, constraints, and open questions, and link authoritative details
rather than duplicating facts.

**One point per line.** Each bullet, numbered item, checkbox, or table cell expresses one clear rule,
decision, or outcome, and each checkbox has one independently verifiable outcome. Prefer one sentence
per point, use a second only to explain or qualify it, and split additional obligations into separate
points rather than hiding them in semicolons or inline lists. Preserve requirement IDs when splitting
their supporting rules.

Write current-state docs in the present tense: do not use "used to" or "no longer" for completed
history. When a Lifecycle trigger requires a migration or deprecation, document the active transition,
its owner, and its trigger; history belongs in `docs/adr/` and git.

Preserve exact limits, exceptions, risks, security boundaries, failure behavior, compatibility,
verification limits, and fixed formats. Remove unused scaffold and filler, and name owners or triggers
for deferred sections. Keep process instructions here and prompts in templates. Use underscores for
emphasis and asterisks for bold; apply `unslop` with its canonical scope and exclusions.

**Briefs and PRDs:** state each requirement once, with only the detail needed for approval and
verification. Briefs explain the problem; PRDs describe observable behavior and testable rules.
Define terms on first use, link implementation decisions to ADRs and contracts, and keep existing
document structure and PRD/ADR introductions intact.

**Code comments:** explain non-obvious intent, constraints, state transitions, and failure behavior
beside the relevant code. Keep them precise and durable; avoid syntax narration and quotas, and link
the reason and the condition that retires a workaround. Change summaries and verification results go in the PR;
a comment claim is not proof.

## Communication standard

Keep user-facing replies compact: lead with the outcome, state each fact once, and omit filler.
Report factual actions, progress, blockers, results, deviations, decisions, and verification evidence.
Never narrate your own constraints or permissions: not what you are avoiding ("I am not polling"), not
what you are permitted to do ("merging is your call"), and not the rule behind an action ("per the gate
protocol"). Turn each one into an ask or an outcome, or delete it. Keep the status header and safety
warnings. Use complete sentences for gates, security warnings, irreversible actions, and complex trade-offs; expand when asked.

## Definition of Ready (before a task enters Implement)

- [ ] Acceptance criteria are written and testable
- [ ] Applicable contract frozen; fast-path N/A recorded when no integration contract applies
- [ ] Frozen contract matches its accepted ADR and the `docs/architecture.md` update
- [ ] No open questions remain (resolved during the Stage 1 stress-test)
- [ ] Task is small enough to ship in ~a day, else split it

## Definition of Done (every task)

- [ ] Meets the acceptance criteria in its PRD/issue
- [ ] Honors frozen contracts; fast-path N/A recorded when no integration contract applies
- [ ] DB schema changes follow expand/contract (migrate → deploy → clean up) **once the table holds real data or any deployed process reads or writes it**; before that, change it outright
- [ ] Verification evidence matches the risk (see `docs/test-strategy.md`). Name the smallest local check that proves the change: links or rendering for documentation changes that affect links or rendering; a diff or one visual check for presentation-only styling, markup, attributes, or copy; focused behavior evidence for styling, markup, or attributes that change accessibility, security, or interaction behavior; syntax, schema, or generation for config or generated output; focused automated tests and runtime observation for non-trivial runtime behavior. Broaden to all impacted packages/modules for shared paths, contracts, or sensitive areas; reserve the full suite for broad or high-risk fan-out or an explicit project rule.
- [ ] **Configured CI is green before merge** (lint, typecheck, test, build, and other required checks). This is a remote merge gate, not a reason to duplicate the suite locally. If CI runs after PR creation, finish local QA and review first. N/A only where no CI workflow exists.
- [ ] `code-review` + `code-simplification` clean; a [sensitive area](#sensitive-areas) also needs `security-review` with complete scoped coverage recorded in `docs/security.md`
- [ ] Diff hygiene: small and focused, references the issue, no stray or debug code
- [ ] Current-behavior claims stay accurate per task; after the final child, reconcile all feature artifacts with implementation evidence
- [ ] Tracker linked and current; closure itself is a post-merge step

## Conventions

- **Stack (placeholder — set at Stage 0):** TypeScript + React and Node are illustrative defaults; replace with your real stack when you fill `docs/context.md`.
- **Branching — GitHub Flow:** `main` is always deployable. Work on short-lived `feat/{id}-{slug}` branches → PR → merge → deploy. Environments are deploy targets driven by CI, not long-lived branches. One feature per branch. A git worktree is an explicit manual escape hatch: the operator supplies a private, new or empty path outside every checkout and runs `feature-start`'s generic Git-only recipe.
- **Where planning commits land.** Land planning packages on `main`, never a feature branch: the Stage 0 context and foundation at the foundation gate, then the Stage 1 PRD plus the Stage 2 ADRs, architecture and security updates, and frozen contract once after Stage 2. Stage 4 cuts `feat/*` from a ref that must already hold the frozen contract, so ask for the landing action by remote state: commit locally with no remote, commit and push to an unprotected `main`, or `plan/{NNNN}-{slug}` → PR for a protected one (`sdlc` → Default-branch landings). Per-task learnings land before the next task; final-child reconciliation lands before the parent epic completes; an empty Retro needs no landing.
- **Commits — Conventional Commits.** `type(scope): summary` — imperative, ≤72 chars. Types: `feat` `fix` `refactor` `test` `docs` `chore` `perf` `build` `ci`. Reference the issue (`Refs #123`, or `Closes #123` on GitHub only, elsewhere its key). Small logical commits, not one blob.
- **PRs:** Keep them small and reviewable; follow the PR template and the conductor's landing gate.
- **History:** Squash-merge feature PRs to keep `main` linear.
- **No agent self-attribution.** Commits, PRs, and code comments describe the _change_, not the tool. No "Made with {agent}" or `Co-Authored-By:` naming an AI. Authorship is the human's; this overrides any runtime default.
- **Contract-first:** define and freeze the interface before FE/BE implement in parallel.
- **Project-facing artifacts cite durable docs, not process mechanics.** Reference "the frozen contract (contract 0001, ADR-0004)" and stop; a reader who never saw this process must not be able to tell it existed. Kit-owned operating docs and templates may describe the process they govern.
- **Ask, don't guess:** if a PRD/ADR is ambiguous, stop and ask rather than assume.
- **A wrong decision is amended, not obeyed.** Follow the conductor's ADR, contract, and scope-reapproval gates.
## Principles

- **Challenge before agreeing.** Never open with agreement. State the approach you rejected and why, the failure you think most likely, and the observation that would settle it. Record the observed result and resulting direction at the applicable gate; an objection without a concrete scenario, file, or command is noise.
- **Simplicity first.** Prefer the smallest direct solution that fully solves the problem; add an abstraction only when a real, present need justifies it, not future speculation.
- **Reuse before building.** Prefer existing, well-maintained libraries over bespoke code when they fit; if unsure, research and weigh fit, maintenance, and footprint first.
- **Pay only for what exists.** Compatibility machinery, migration/deprecation guidance, and tests for production-only conditions protect a real consumer, real data, traffic, or an observed incident, not a hypothetical one. Read the Lifecycle block in `docs/context.md` first: while the applicable trigger condition is absent, cover non-trivial executable behavior and record only deferrals whose required deployed consumer, real data, deployment, load, traffic, or multi-version compatibility is unavailable in the production register. If something outside this change might depend on it, ask.

## Sensitive areas

**Canonical list** (other docs and skills point here): **authentication, authorization, payments,
PII/KYC, file uploads, and admin/privileged surfaces.** A change touching these updates
`docs/security.md` and gets `security-review` before each planning or implementation merge.

## Vendored skill overrides

Third-party snapshots supply techniques; this file and the `sdlc` conductor own paths, transitions, and safety. Run stage-bound snapshots only when `sdlc` routes to them, and apply these overrides:

- Before using the `brainstorming` visual companion, set `SUPERPOWERS_DISABLE_TELEMETRY=1` to block its branding request. Keep it on loopback with an SSH tunnel, never plaintext non-loopback mode; use its default temporary session directory and do not pass `--project-dir`. Ignore its instruction to commit or write under `docs/superpowers/`.
- For `improve-codebase-architecture`, treat `CONTEXT.md` as `docs/context.md`; do not invoke its unavailable `codebase-design` or `domain-modeling` dependencies, and skip its CDN-backed report.
- For an opt-in worktree, use the generic Git-only `git worktree add` and non-forced `git worktree remove` commands in `feature-start`; the operator owns platform-specific path selection, privacy, and containment checks.
- Do not use `webapp-testing`'s bundled `with_server.py`; use the project's lifecycle runner or an already-running server. Wait for an app-specific readiness signal, not mandatory `networkidle`.

## Guardrails

> These rules depend on agent adherence, CI, and review gates; this file alone enforces nothing.

- Do not commit, push, or open PRs unless asked. The human performs every landing merge; local default-branch synchronization by `git merge --ff-only` and review-only integration commits are not landing merges.
- At Land, don't poll CI: open the PR and report CI running, or push the branch to start CI, then stop. Don't `gh run watch`. Required CI must be green before merging.
- Don't improvise git transports or remote URLs. If a GitHub HTTPS push fails on auth, surface it and point to `gh auth login` then `gh auth setup-git`. Change a remote URL only after the human approves the reviewed URL, using `git remote set-url origin {url}`; never silently switch transports.
- Do not change a shipped contract with a deployed consumer without a versioning/deprecation decision (a new ADR); if there is no deployed consumer, apply the ADR matrix and re-freeze the contract.
- Do not write a breaking DB migration against a table holding real data or read/written by any deployed process; use expand/contract so `main` stays deployable through the rollout.
- A change touching a [sensitive area](#sensitive-areas) gets a threat model + `security-review`.

## Outcome summaries

For tasks needing manual verification (UI, flows, integrations), end with a short **QA checklist** of
steps and expected results; skip it when fully tested.
