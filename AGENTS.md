# AGENTS.md — Operating manual for AI agents on this project

> Canonical agent instructions. `CLAUDE.md`, `.cursorrules`, and similar files should be a single
> line pointing here. **Keep it lean and current** — read every session, so every line costs
> attention and tokens (target ≤150 lines). Single-source: point to the doc/skill, don't restate it.

## What this project is

<!-- One paragraph: product, users, current phase. Link docs/context.md for depth. -->
See [`docs/context.md`](./docs/context.md) for domain, glossary, personas, and hard constraints.

## Two altitudes: foundation vs feature

Artifacts come at two altitudes — don't conflate them:

- **Foundation (project-level)** — set once at **Stage 0**: product PRD (`docs/prd/0000-product.md`),
  the few cross-cutting **ADRs** (stack, repo, auth, datastore, API style), the architecture
  skeleton, and the core contract. What a first feature can't start without — keep it minimal.
- **Feature-level** — per feature (Stages 1–8): a brief, a feature PRD, feature ADR(s), a contract
  *slice*. Let most ADRs/contracts emerge as you build, not guessed up front.

## How we work: the plan-gated pipeline

We build features through a fixed pipeline. The **conductor skill** (`sdlc`) routes each stage.
You MUST stop at every **gate** (✅) below and get explicit human approval before proceeding —
never skip a gate to "save time." Non-gate stages are **proceed-with-disclosure**: do the work,
report what you did and any decision worth overriding, and continue without waiting. **Every
response while a feature is in the pipeline** opens with a one-line **status header**
(`SDLC ▸ Stage {N}/8 {Name} · {next gate or action}`) — whichever skill is driving the turn (`sdlc`,
`feature-start`, or a stage skill) — so the current stage and next gate stay visible.

| Stage | You produce | Gate |
|-------|-------------|------|
| 0 — Context + Foundation | filled `docs/context.md`; product PRD + foundational ADRs + architecture skeleton + core contract | ✅ approve foundation |
| 1 — Spec | *(optional)* brief `docs/briefs/NNNN-*` for a fuzzy idea → hardened PRD in `docs/prd/` (no issues yet) | ✅ approve PRD |
| 2 — Architecture + Contract | ADR(s), updated `docs/architecture.md`, `docs/security.md` (sensitive areas), **frozen** contract artifact | ✅ approve approach + freeze |
| 3 — Decompose | tracker issues (GitHub by default; the tracker is the record) | disclose breakdown |
| 4 — Implement | code on a `feat/*` branch, one task at a time | ✅ plan per task |
| 5 — QA | tests green + app runs + CI green | — |
| 6 — Review | clean diff, findings fixed (`security-review` if sensitive) | inline — no gate |
| 7 — Land | PR opened where hosting supports it. Without PR support, push the branch if a remote exists, run any available CI, and the human merges it directly; with no remote, the human merges the local branch. **GitHub:** carries `Closes #N`, issue closes on merge. **Any other tracker / local-only:** no keyword — task → *In review*, completed after the merge (see `sdlc` skill) | ✅ human merges |
| 8 — Retro | 0–3 durable learnings curated into `docs/context.md` (prune while you're there) | — |

> Not every change runs all stages. **Right-size the process:** features run the full pipeline
> (0→8); bug fixes go Implement → QA → Review; chores go Implement → Review. A change graduates to
> the full path the moment it touches a contract, a security-sensitive area, or makes a decision.

## Where things live

- **Product PRD** (project-level vision/scope, set at Stage 0) → `docs/prd/0000-product.md`
- **Feature PRDs** → `docs/prd/NNNN-{slug}.md` (numbered from 0001, status-tracked)
- **ADRs** (decision history, append-only) → `docs/adr/NNNN-{slug}.md` — *foundational* ADRs
  (stack/repo/auth/datastore/API) are set at Stage 0; *feature* ADRs are added per feature
- **Architecture** (current system shape, living) → `docs/architecture.md`
- **Contracts** (the integration source of truth) → in the codebase (`api/openapi.yaml`,
  tRPC routers, `schema.prisma`, Zod schemas). See `docs/contracts/README.md`.
- **Task status** → your tracker (GitHub Issues/Projects), the single source of truth, reported live
  by `project-status`. *Local-only (no tracker):* `docs/progress.md` **is** the tracker
- **Test strategy + Definition of Done** → `docs/test-strategy.md`

## Definition of Ready (before a task enters Implement)

- [ ] Acceptance criteria are written and testable
- [ ] The contract it implements against is defined and frozen
- [ ] No open questions remain (resolved during stress-test, at the Spec gate)
- [ ] Task is small enough to ship in ~a day (else split it)

## Definition of Done (every task)

- [ ] Meets the acceptance criteria in its PRD/issue
- [ ] Implements against the frozen contract (no silent contract changes)
- [ ] DB schema changes follow expand/contract (migrate → deploy → clean up) **once the table holds
      real data or any deployed process reads or writes it** — before that, change it outright
- [ ] Tests at the right layer (see `docs/test-strategy.md`); suite is green
- [ ] App runs and the change is observed working (not just unit-green)
- [ ] **CI is green** (lint, typecheck, test, build) — N/A *only* where no CI workflow exists;
      CI that exists but is unreachable blocks, it doesn't exempt. When CI needs a pushed branch,
      you don't push unless asked: local QA + review, then stop at the push — not back at Stage 4.
- [ ] `code-review` + `simplify` clean; a [sensitive area](#sensitive-areas) also needs
      `security-review` run and `docs/security.md` updated
- [ ] Diff hygiene: small and focused, references the issue, no stray/debug code
- [ ] Docs updated: `architecture.md` if shape changed, ADR if a decision was made
- [ ] Tracker linked and current (rules by tracker/hosting: see the Stage 7 row above) — closure
      itself is a post-merge step, not required before Land

## Conventions

- **Stack (placeholder — set at Stage 0):** TypeScript + React (frontend), Node (backend) are
  illustrative defaults. Replace with your real stack when you fill `docs/context.md`.
- **Branching — GitHub Flow:** `main` is always deployable. Work on short-lived
  `feat/{issue#}-{slug}` (or `fix/...`) branches → PR → merge → deploy. Environments
  (preview/staging/prod) are deploy targets driven by CI, not long-lived branches. One feature per
  branch; default to it — reach for a git worktree only when isolation is critical (parallel/disposable).
- **Where planning commits land.** Stage 0–2 artifacts (foundation docs, PRD, ADRs, frozen
  contract) are gated, approved decisions → ask to commit them to **`main`** at their gate, not a
  feature branch. Stage 4 then cuts `feat/{issue#}-{slug}` from a clean `main` already holding the
  frozen contract (what lets FE/BE build in parallel) — only *code* lives on the branch; a frozen
  contract changes only via a new ADR. If `main` is PR-protected, use `plan/{NNNN}-{slug}` → PR →
  merge, then branch `feat/*`. **Stage 8 retro learnings** land the same way, **before the next
  feature branches**, so nothing is left stashed when `feature-start` needs a clean tree.
- **Commits — Conventional Commits.** `type(scope): summary` — imperative, ≤72 chars. Types:
  `feat` `fix` `refactor` `test` `docs` `chore` `perf` `build` `ci`. Reference the issue
  (`Refs #123` / `Closes #123` — GitHub only; elsewhere its key). Small logical commits, not a blob.
- **PRs:** small and reviewable; one feature per branch; reference the issue; fill the PR template
  (acceptance criteria, contract, DoD, security). Squash-merge to keep `main` linear.
- **No agent self-attribution.** Commits/PRs describe the *change*, not the tool that made it — no
  "Made with {agent}", "Generated by …", or `Co-Authored-By:` trailer naming an AI, in commits, PR
  titles/bodies, or code comments. Authorship is the human's; this overrides any runtime default.
- **Contract-first:** define and freeze the interface before FE/BE implement in parallel.
- **Comments cite docs, not stages.** Reference the durable artifact — "the frozen contract
  (contract 0001, ADR-0004)", never "frozen at Stage 2", which means nothing outside this process.
- **Ask, don't guess:** if a PRD/ADR is ambiguous, stop and ask rather than assume.

## Principles

- **Simplicity first.** Prefer the smallest direct solution that fully solves the problem; add an
  abstraction only when a real, present need justifies it — not future speculation.
- **Reuse before building.** Prefer existing, well-maintained libraries over bespoke code when they
  fit; if unsure, research and weigh the options (fit, maintenance, footprint) first.
- **Don't pre-build back-compat.** Expand/contract, API versioning, and backfills protect a real
  consumer or real data already depending on the current shape — not a hypothetical future one. If
  you don't know whether something outside this change depends on it, ask; don't assume either way.

## Sensitive areas

The **canonical list** — other docs and skills reference this rather than restating it:
**authentication, authorization, payments, PII/KYC, file uploads, and admin/privileged surfaces.**
A change touching any of these gets a threat-model pass at Architecture (recorded in
`docs/security.md`) and a `security-review` before merge.

## Guardrails

> These are *guidance*, not a runtime guarantee. Enforcement = agent adherence + CI + the review
> gates and checklists. `AGENTS.md` existing does not by itself enforce anything.

- Do not commit, push, open PRs, or **merge** unless asked — **merge is always the human's call.**
- **At Land, don't poll CI.** With a PR workflow, open the PR and report CI running. With CI but no
  PR workflow, push the branch to start CI and report the run. Then stop at the human merge gate —
  don't `gh run watch` or keep the turn polling. Required CI must be green before the human merges.
- Don't improvise git transports or remote URLs. If a push fails on auth, **surface it and point to
  the one-time fix** (`gh auth setup-git`, or the SSH→HTTPS rewrite in INSTALL.md) — never silently
  push via an ad-hoc HTTPS URL.
- Do not change a *shipped* contract without a versioning/deprecation decision (new ADR).
- Do not write a breaking DB migration against a table holding real data or read/written by any
  deployed process — use expand/contract so `main` stays deployable through the rollout.
- A change touching a [sensitive area](#sensitive-areas) gets a threat model + `security-review`.

## Outcome summaries

When you finish a task worth manual verification (UI, user flows, integrations — anything not fully
covered by tests), end the summary with a short **QA checklist**: concrete steps a human can follow
(what to do, what to expect), not a restatement of what you did. Skip it when fully tested.
