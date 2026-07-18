# SDLC pipeline — team cheatsheet

A one-page field guide to how we build. Not the install steps — the pieces to keep in your head
while working. Depth lives in `AGENTS.md`; the conductor (`sdlc` skill) drives it.

## The pipeline (0 → 8)

| # | Stage | You produce | Gate? |
|---|-------|-------------|-------|
| 0 | **Context + Foundation** | filled `docs/context.md`; product PRD + foundational ADRs + architecture skeleton + core contract | ✅ approve foundation |
| 1 | **Spec** | brief → hardened PRD in `docs/prd/` (no issues yet) | ✅ approve PRD |
| 2 | **Architecture + Contract** | ADR(s), updated `architecture.md`, `security.md`, **frozen** contract | ✅ approve + freeze |
| 3 | **Decompose** | tracker issues (GitHub by default; tracker is the record) | disclose |
| 4 | **Implement** | code on a `feat/*` branch, one task at a time | ✅ plan per task |
| 5 | **QA** | tests green, app runs, CI green | — |
| 6 | **Review** | clean diff, findings fixed | inline (security-review if sensitive) |
| 7 | **Land** | PR if supported; otherwise push iff a remote exists, run CI if available, and the human merges directly. **GitHub:** PR carries `Closes #N`, closes on merge. **Other trackers / local-only:** no `#N` keyword — task → *In review*, then closed/*Done* after the merge | ✅ **human merges** |
| 8 | **Retro** | learnings appended to `context.md` | — |

## The 5 hard gates — STOP and get a human "yes"

Foundation · Spec (PRD) · Architecture+Contract · per-task Implement plan · **merge**.
Everything else is **proceed-with-disclosure**: do the work, say what you did + any call worth
overriding, keep moving. Never skip a ✅ to save time. Merge is *always* the human's call.

## Right-size the path — don't run all 9 for everything

- **Feature / user-facing / risky** → full pipeline `0 → 8`.
- **Bug fix / small enhancement** → `4 Implement → 5 QA → 6 Review` (reference an issue).
- **Chore / docs / dep bump** → `4 → 6`, trivial diff, CI green.
- Graduates to full path the moment it touches a **contract**, a **sensitive area**, or makes a
  **decision**. When unsure, ask.

## Two altitudes — don't conflate them

- **Foundation (project-level, set once at Stage 0):** product PRD, cross-cutting ADRs
  (stack/repo/auth/datastore/API style), architecture skeleton, core contract. Lock only what a
  first feature can't start without.
- **Feature-level (per feature, Stages 1–8):** brief, feature PRD, feature ADR(s), a contract *slice*.
- Don't design every feature up front — let the rest emerge as you build.

## Contract-first — the rule that keeps FE/BE in sync

1. Define/extend the contract **before** implementing (Stage 2).
2. **Freeze** it at the gate → FE and BE build against it in parallel.
3. **Generate** types from it; never hand-duplicate on each side.
4. Changing a **shipped** contract = a decision → new ADR (versioning/deprecation). No silent breaks.

## Sensitive areas → threat-model + security-review are mandatory

The canonical list lives in **`AGENTS.md` → Sensitive areas**. Any change touching one gets a
threat-model pass at Stage 2 (`docs/security.md`) AND a `security-review` at Stage 6 before merge.
Not agent-discretion — mandatory.

## Definition of Ready (before Implement)

Acceptance criteria written & testable · contract frozen · no open questions · task ships in ~a day.

## Definition of Done (every task)

Meets AC · implements the frozen contract · expand/contract migrations (once the table holds real
data or any deployed process reads or writes it) · tests green at the right layer · app observed ·
**CI green** (N/A only where no CI workflow exists — unreachable CI blocks, not exempts) ·
`code-review` + `simplify` clean (+ `security-review` if sensitive) ·
docs updated (`architecture.md` / ADR) · issue links the PR, closes on merge (local-only:
`progress.md`).

## Git & commits

- **GitHub Flow:** `main` always deployable. Short-lived `feat/{issue#}-{slug}` → PR → merge → deploy.
  Environments are deploy targets, not long-lived branches. **Default to a branch** (worktree only
  when isolation is genuinely critical).
- **Conventional Commits:** `type(scope): summary` (imperative, ≤72 chars). Types: `feat` `fix`
  `refactor` `test` `docs` `chore` `perf` `build` `ci`. Reference the issue (`Refs #123` /
  `Closes #123`) — GitHub only; another tracker uses its key, and local-only ids aren't issues.
- Small logical commits, not one blob. PRs small & reviewable, one feature per branch, squash-merge.
- **Where planning commits land:** Stage 0–2 docs (PRD, ADRs, frozen contract) are
  gated decisions → commit to **`main`** at their gate. Cut `feat/*` from a clean `main` that already
  holds the frozen contract (so FE/BE build against it in parallel); only *code* lives on the branch.
  PR-protected `main`? Use a `plan/*` branch → PR → merge, then branch `feat/*`.

## Where things live

`docs/context.md` (domain) · `docs/prd/0000-product.md` (product) · `docs/prd/NNNN-*` (features) ·
`docs/adr/NNNN-*` (decisions) · `docs/architecture.md` (current shape) · `docs/contracts/` (integration
truth) · `docs/security.md` · `docs/test-strategy.md`. Task status → your tracker (no in-repo mirror).

## Beyond the pipeline (optional)

After an **epic closes**, the `improve` companion skill (read-only, standalone, not gated) surveys
what you built. **Audit** (default) writes *fix* plans to `plans/` (bugs/debt/perf/tests; ephemeral —
gitignore or delete after); land them as **dependency-ordered PRs — human still merges each**.
**`improve next`** → treat as **informational**: decline its plan-writing step and hand the chosen
direction to **Stage 1** (it writes design/spike plans only if you let it). Never merges. A companion
to the pipeline, not part of it.

## Reflexes

- Ambiguous PRD/ADR → **stop and ask**, don't guess.
- Keep the relevant doc (`architecture.md` / ADR) current as you go; task status lives in the tracker.
- Watch the conductor's status header — `SDLC ▸ Stage {N}/8 {Name} · {next gate}` — to know where you are.
