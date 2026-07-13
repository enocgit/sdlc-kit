# AGENTS.md — Operating manual for AI agents on this project

> Canonical agent instructions. `CLAUDE.md`, `.cursorrules`, and similar files should be a
> single line pointing here. **Keep it lean and current** — it's read at the start of *every*
> session, so every line costs attention and tokens (target ≤150 lines). Single-source: point to
> the relevant doc or skill rather than restating it here.

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
| 7 — Land | PR opened; tracker updated (issue closed) | ✅ human merges |
| 8 — Retro | learnings appended to `docs/context.md` | — |

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
- **Task status** → your tracker (GitHub Issues/Projects), the single source of truth;
  `project-status` reports it live. *Local-only (no tracker):* `docs/progress.md` **is** the tracker
- **Test strategy + Definition of Done** → `docs/test-strategy.md`

## Definition of Ready (before a task enters Implement)

- [ ] Acceptance criteria are written and testable
- [ ] The contract it implements against is defined and frozen
- [ ] No open questions remain (resolved during stress-test, at the Spec gate)
- [ ] Task is small enough to ship in ~a day (else split it)

## Definition of Done (every task)

- [ ] Meets the acceptance criteria in its PRD/issue
- [ ] Implements against the frozen contract (no silent contract changes)
- [ ] DB schema changes follow expand/contract (backward-compatible migrate → deploy → clean up)
- [ ] Tests at the right layer (see `docs/test-strategy.md`); suite is green
- [ ] App runs and the change is observed working (not just unit-green)
- [ ] **CI is green** (lint, typecheck, test, build — the mechanical half). CI needs a pushed branch
      you don't push unless asked; finish local QA + review, then stop at the push — not back at Stage 4.
- [ ] `code-review` + `simplify` clean; if the change touches a **sensitive area** (see
      [Sensitive areas](#sensitive-areas)), `security-review` was run and `docs/security.md` updated
- [ ] Diff hygiene: small and focused, references the issue, no stray/debug code
- [ ] Docs updated: `architecture.md` if shape changed, ADR if a decision was made
- [ ] The tracker issue updated (status / closed) — no in-repo mirror to maintain

## Conventions

- **Stack (placeholder — set at Stage 0):** TypeScript + React (frontend), Node (backend) are
  illustrative defaults. Replace with your real stack when you fill `docs/context.md`.
- **Branching — GitHub Flow:** `main` is always deployable. Work on short-lived
  `feat/{issue#}-{slug}` (or `fix/...`) branches → PR → merge → deploy. **Environments
  (preview/staging/prod) are deploy targets driven by CI, not long-lived branches.** One feature
  per branch. **Default to a branch**; reach for a git worktree only when isolation is critical
  (parallel or disposable work).
- **Where planning commits land.** Stage 0–3 artifacts (foundation docs, PRD, ADRs, frozen
  contract) are gated, approved decisions → commit to **`main`** at their gate, not a feature
  branch. Stage 4 then cuts `feat/{issue#}-{slug}` from a clean `main` that already holds the frozen
  contract (what lets FE/BE build in parallel) — only *code* lives on the branch; a frozen contract
  changes only via a new ADR. If `main` is PR-protected, use a `plan/{NNNN}-{slug}` → PR → merge,
  then branch `feat/*`. **Stage 8 retro learnings** (`docs/context.md`) land on `main` the same way,
  **before the next feature branches**, so a learning isn't stashed when `feature-start` needs a
  clean tree.
- **Commits — Conventional Commits.** `type(scope): summary` — imperative, ≤72 chars. Types:
  `feat` `fix` `refactor` `test` `docs` `chore` `perf` `build` `ci`. Reference the issue
  (`Refs #123` / `Closes #123`). Small logical commits, not one blob.
- **PRs:** small and reviewable; one feature per branch; reference the issue; fill the PR template
  (acceptance criteria, contract, DoD, security). Squash-merge to keep `main` linear.
- **No agent self-attribution.** Commit messages and PR descriptions describe the *change*, not the
  tool that made it. Do not add "Made with {agent}", "Generated by …", a `Co-Authored-By:` trailer
  naming an AI, or similar — in commits, PR titles/bodies, or code comments. The work is the team's;
  authorship is the human's. (This overrides any runtime default that appends such a footer.)
- **Contract-first:** define and freeze the interface before FE/BE implement in parallel.
- **Comments cite docs, not stages.** Reference the durable artifact (ADR/PRD/contract), never the
  pipeline stage — "frozen at Stage 2" goes stale and means nothing outside this process. Write
  "the frozen contract (contract 0001, ADR-0004)".
- **Ask, don't guess:** if a PRD/ADR is ambiguous, stop and ask rather than assume.

## Principles

- **Simplicity first.** Prefer the smallest direct solution that fully solves the problem; add an
  abstraction only when a real, present need justifies it — not future speculation.
- **Reuse before building.** Prefer existing, well-maintained libraries over bespoke code when they
  fit; if unsure, research and weigh the options (fit, maintenance, footprint) first.

## Sensitive areas

The **canonical list** — other docs and skills reference this rather than restating it:
**authentication, authorization, payments, PII/KYC, file uploads, and admin/privileged surfaces.**
A change touching any of these gets a threat-model pass at Architecture (recorded in
`docs/security.md`) and a `security-review` before merge.

## Guardrails

> These are *guidance*, not a runtime guarantee. Enforcement = agent adherence + CI + the review
> gates and checklists. `AGENTS.md` existing does not by itself enforce anything.

- Do not commit, push, open PRs, or **merge** unless asked — **merge is always the human's call.**
- **At Land, don't block on CI.** Open the PR, report it's running, and stop — don't `gh run watch`
  or keep the turn polling. Branch protection blocks a red merge; a later failure is just a normal fix.
- Don't improvise git transports or remote URLs. If a push fails on auth, **surface it and point
  the user to the one-time fix** (`gh auth setup-git`, or the SSH→HTTPS rewrite in INSTALL.md) —
  don't silently push via an ad-hoc HTTPS URL.
- Do not change a *shipped* contract without a versioning/deprecation decision (new ADR).
- Do not write a breaking DB migration — use expand/contract so `main` stays deployable.
- A change touching a [sensitive area](#sensitive-areas) gets a threat model + `security-review`.

## Outcome summaries

When you finish a task worth manual verification (UI, user flows, integrations — anything not fully
covered by tests), end the summary with a short **QA checklist**: concrete steps a human can follow
(what to do, what to expect), not a restatement of what you did. Skip it for trivial or
fully-tested changes.
