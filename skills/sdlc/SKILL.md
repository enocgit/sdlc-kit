---
name: sdlc
description: >
  Orchestrates an end-to-end, plan-gated software build pipeline: routes each stage to the right
  skill while enforcing human approval gates. Covers discovery, PRD, stress-test, architecture,
  API contracts, decomposition, implementation, QA, review, landing, and retro. The single entry
  point for the workflow. Use when the user wants to build a feature or product the disciplined
  way, start or resume structured development, asks "what stage are we at" / "what's next", or
  says "start the sdlc" / "run the pipeline".
---

# sdlc — the conductor

You are running a fixed, plan-gated pipeline. Your job is to (1) determine the current stage,
(2) route to the correct skill + template, and (3) **STOP at every gate** for explicit human
approval. You guide; you do not silently skip ahead.

## Two altitudes (read this first)

Artifacts live at two altitudes — keep them straight:

- **Project-level (foundation)** — set once, early (Stage 0): the **product PRD**
  (`docs/prd/0000-product.md`), the few cross-cutting **ADRs** (stack, repo layout, auth,
  datastore, API style), the **architecture skeleton**, and the **core contract**. These belong
  to no single feature.
- **Feature-level** — produced per feature (Stages 1–8): a brief, a feature PRD, feature ADR(s),
  and a contract *slice*.

Don't design every feature up front — but DO lock the handful of foundational decisions a first
feature can't start without. Let everything else emerge per-feature.

## First: orient

**Resolve skills from the skill dirs.** Look for this pipeline's skills in the user-global
dirs (`~/.agents/skills`, `~/.claude/skills`) **and** the project's local skills dir — not the
project alone. A skill may be installed globally; don't assume a stage's skill is missing just
because it isn't vendored in the repo. If it's in neither place, resolve in this order: (1) use the
named skill if present; (2) else use your **runtime's equivalent** — several stage skills are named
after Claude Code's commands (`code-review`, `simplify`, `verify`, `run`, `security-review`) and other
runtimes have their own (e.g. Codex `review` ≈ `code-review`), so use that; (3) only if there's no
skill **and** no runtime equivalent, use the manual `fallback` in `required-skills.yml`.

1. Read `AGENTS.md` and `docs/context.md`. **Stage 0 is incomplete** if either is missing OR
   still contains template markers — an unfilled `docs/context.md` carries a `> STATUS: TEMPLATE`
   line and/or `{placeholder}` tokens. The installer ships these files pre-created, so do NOT
   rely on existence alone: check the context is actually filled. If Stage 0 is incomplete, run
   the on-ramp and treat **"context filled" as a gate** — do not advance to Discovery until the
   STATUS marker is gone and the sections are completed for this project:
   - **`bootstrap` (new project, little/no code):** two parts —
     - **0a Context:** the kit's installer already scaffolded `docs/`, `AGENTS.md`, and the
       one-line `CLAUDE.md` pointer — if any are missing, re-run the kit's `install.sh` (it's
       non-destructive) rather than recreating them by hand. Then interactively fill
       `docs/context.md`. Do NOT run `init` — there's no codebase yet. *Gate: context filled.*
     - **0b Foundation:** produce the **project-level** artifacts — a product PRD at
       `docs/prd/0000-product.md`, the few unavoidable cross-cutting ADRs (stack, repo layout,
       auth, datastore, API style), the `architecture.md` skeleton, and a core contract scaffold.
       Keep it minimal: only decisions a first feature genuinely can't start without — let the
       rest emerge per-feature. **GATE: approve the foundation before Discovery.**
   - **`adopt` (existing codebase):** run `improve-codebase-architecture` (and `init`) to
     reverse-engineer `context.md` + `architecture.md` and **backfill the foundational ADRs**
     (stack, repo, auth, datastore already baked into the code). That reverse-engineered set IS
     the project-level foundation. Note known **tech-debt / risky areas** in `architecture.md`
     (and file actionable ones as issues); the first feature to validate the workflow is simply
     your first Stage 1 Spec. **GATE: approve.**
   - **If these files already exist** (`AGENTS.md`/`CLAUDE.md`/`docs/`), do NOT overwrite. Merge:
     back up or section-merge, preserve the team's content, surface conflicts. Never clobber.
2. **Right-size the path.** Classify the change before routing:
   - **Feature / user-facing / risky** → full pipeline (0→8).
   - **Bug fix / small enhancement** → skip to **4 Implement → 5 QA → 6 Review** (reference an
     issue; no PRD/contract/ADR).
   - **Chore / docs / dep bump** → **4 → 6**, trivial diff, CI green.
   - The moment a "small" change touches a **contract**, a **security-sensitive area**, or makes
     a **decision**, it graduates to the full path. When unsure, ask.
3. Read the tracker (via `gh` / `project-status`) and the active PRD to infer the current stage and
   feature (local-only mode: read `docs/progress.md`).
4. State the chosen path, current stage, and next action to the user before proceeding.

## Status header (every response)

Open every substantive response with one compact line, so the user — and you — always know where
the pipeline is:

`SDLC ▸ Stage {N}/8 {Name} · {next gate or action}`

Examples (on-ramp sub-stages keep their letter — `0a`/`0b`/`0adopt`):
- `SDLC ▸ Stage 0b/8 Foundation · next gate: approve foundation`
- `SDLC ▸ Stage 1/8 Spec · next gate: approve PRD`
- `SDLC ▸ Stage 4/8 Implement · task #5 · next: plan approval`
- `SDLC ▸ Stage 6/8 Review · running security-review (sensitive area)`

One line only; skip it only for trivial acknowledgements. It doubles as your own anchor — restating
the stage each turn is what keeps you from drifting off-process over a long conversation.

## Borrow the technique, not the workflow

The community skills below are **techniques**, not the pipeline. Each was authored standalone and
carries its own opinions about *where it writes* and *what it does next* — those opinions are wrong
here, because **this conductor owns the workflow.** When you run a borrowed skill, use its method
and **override its workflow**:

- `brainstorming` → use its discovery method (explore → **one question at a time** → approaches →
  design), but land the artifact as the **(optional) Stage-1 brief** at `docs/briefs/NNNN-{slug}.md`
  and STOP. Reach for brainstorming + a brief only when the idea is fuzzy; a well-understood feature
  skips both and goes straight to `to-prd`.
  Discovery is exploratory — **no code.** Do **not** write to `docs/superpowers/specs/`, and do
  **not** auto-run `writing-plans`; the next step is the Stage 1 Spec (`to-prd`), then the gate.
- `documentation-and-adrs` → ADRs go to **`docs/adr/NNNN-{slug}.md`** (this project's convention),
  never `docs/decisions/`.
- Any skill that wants to open tracker issues/epics → **defer to Stage 3 Decompose.** The Spec stage
  produces a PRD, not issues.

If a borrowed skill's default fights an `AGENTS.md` convention, **`AGENTS.md` wins.**

## The stages, skills, and gates

| Stage | Use skill | Output | After producing output |
|-------|-----------|--------|------------------------|
| 0a Context (new) | installer-scaffolded templates (fill) | `AGENTS.md`, filled `docs/context.md` | gate: context filled |
| 0b Foundation (new) | `documentation-and-adrs` | `docs/prd/0000-product.md`, foundational ADRs (→ `docs/adr/`), `architecture.md` skeleton, core contract scaffold (**trim `docs/contracts/README.md`** to real/`(future)` paths — never leave template examples) | **GATE — approve foundation** |
| 0 adopt (existing) | `improve-codebase-architecture` + `init` | reverse-engineered context/architecture + backfilled foundational ADRs (**point `docs/contracts/README.md` at the existing contract source**; note tech-debt/risks in `architecture.md`) | **GATE — approve** |
| 1 Spec | `brainstorming` (method only) → `to-prd` → `grill-me` | **optional** Stage-1 brief `docs/briefs/NNNN-*.md` (only for a fuzzy/speculative idea — else skip straight to the PRD), then hardened PRD `docs/prd/NNNN-*.md` (no issues yet) | **GATE — approve PRD** |
| 2 Architecture + Contract | `documentation-and-adrs` | ADR(s) in `docs/adr/`, updated `docs/architecture.md`, `docs/security.md` (sensitive areas), **frozen** contract artifact in repo (OpenAPI/tRPC/schema) | **GATE — approve approach + freeze interface** |
| 3 Decompose | `writing-plans` + `project-status` | **tracker issues** (GitHub by default) shaped per `.github/ISSUE_TEMPLATE/{epic,task}.md` (the tracker is the record — no in-repo mirror; other trackers: their native issue types; local-only: task list in `docs/progress.md`) | disclose the breakdown, then continue |
| 4 Implement | `feature-start` (branch; `using-git-worktrees` only if isolation is critical) → `executing-plans`, `frontend-design` (UI work only) | code on a `feat/*` branch, one task at a time | **GATE — plan per task** |
| 5 QA | `test-driven-development`, `run`, `verify` (`webapp-testing` for UI/browser) | tests green, app runs, CI green | proceed (disclose results) |
| 6 Review | `code-review`, `simplify`, `definition-of-done-review` — pick what the change warrants | clean diff, findings fixed | inline, no gate — but **`security-review` is mandatory if a sensitive area is touched** |
| 7 Land | `project-status` | PR opened; the tracker reflects it (issue closed via `Closes #N`) | **GATE — the human merges** |
| 8 Retro | reflect + write (native) | learnings appended to `docs/context.md` (+ optional agent memory) | surface the change + recommend landing `context.md` on `main` (offer; don't auto-commit) before the next feature — then done |

## Gate protocol (non-negotiable)

At every **GATE**, do ALL of the following and then halt:
1. Name the artifact you produced and its path.
2. Summarize what's in it in 2–4 lines.
3. Say exactly what the next stage will do.
4. Ask: "Approve to proceed, or tell me what to change?"

Do not run the next stage's skill until the user approves. Skills are guidance injected into
context — only YOU enforce these stops, so be explicit every time.

**Gates vs. proceed-with-disclosure.** Only the **GATE** rows are hard stops: Foundation, Spec,
Architecture+Contract, the per-task Implement plan, and the human merge at Land. The remaining
stages (Decompose, QA, Review) are **proceed-with-disclosure**: do the work, then state what you
did and any decision a human might want to override, and continue — don't wait. The human can
always interrupt. This keeps the front half rigorous and the back half moving.

**The Stage 5 CI seam — don't over-stop.** Stage 5's "CI green" needs a pushed branch, but the
guardrail says don't commit/push/PR unless asked. That is **one narrow stop at the commit/push
boundary — not a reason to stop at the end of Stage 4.** After the Implement plan gate, keep going
through everything that needs *no* push: local tests, `run`/`verify`, and the whole Stage 6 pass
(`code-review`, `simplify`, `security-review` if sensitive, diff hygiene). Only *then* stop, at the
push, and disclose: *"local checks + review done; CI green is pending your approval to commit/push."*
The remaining Stage 5 item (CI green) and the Land merge both complete after you're cleared to push.

## Rules

- **GitHub Flow:** `main` is always deployable. Work on short-lived `feat/{issue#}-{slug}`
  branches → PR → merge → deploy. Environments are deploy targets, not long-lived branches.
- **Default to a feature branch.** Use a git worktree (`using-git-worktrees`) only when isolation
  is genuinely critical — parallel or disposable work — not as the default.
- **Planning commits land on `main`.** Stage 0–3 artifacts are gated decisions: when committed they
  belong on `main`, not a feature branch. Land them at each gate so Stage 4 branches from a clean
  `main` that already holds the frozen contract — only code lives on the `feat/*` branch. If `main`
  is PR-protected, use a `plan/*` branch → PR → merge, then branch `feat/*`. **Stage 8 retro
  learnings** (`docs/context.md`) land on `main` the same way, before the next feature branches.
  (See `AGENTS.md` → Where planning commits land.)
- One feature in flight per branch. Reference the tracker issue (its `#`/key) in commits/PRs.
- At Decompose, create issues with `gh issue create` and **shape their bodies to match**
  `.github/ISSUE_TEMPLATE/{epic,task}.md` — one `epic` per feature, a `task` per child. (`--body`
  bypasses the template, so follow its structure by hand: reference line → Scope/Tasks → DoD.)
- **Definition of Ready** before Stage 4: acceptance criteria written, contract frozen, no open
  questions. **Definition of Done** before Land (Stage 7) (see `AGENTS.md`).
- Contract-first: never let implementation drift from the frozen contract. Changing a shipped
  contract requires a new ADR (versioning/deprecation).
- **Reviews run inline** during Implement/QA — pick `code-review` / `simplify` /
  `definition-of-done-review` as the change warrants. `security-review` is **mandatory** (not
  agent-discretion) whenever a sensitive area is touched.
- Sensitive areas (canonical list in `AGENTS.md` → Sensitive areas): threat-model at Stage 2
  (`docs/security.md`) AND `security-review` at Stage 6.
- DB schema changes follow expand/contract (backward-compatible migrate → deploy → clean up).
- If a PRD/ADR is ambiguous, stop and ask — do not guess.
- Keep the relevant doc (`architecture.md` / ADR) updated as you go; task status lives in the
  tracker (no in-repo mirror), reported via `project-status`.
- **At Land, don't block on CI.** Open the PR, report it's open with CI running (a *single*
  `gh pr checks` glance to catch an instant failure is fine), then **stop — return to the human merge
  gate.** Don't watch the run to completion (`gh run watch`) or keep the turn alive polling. Branch
  protection blocks a red merge and the human sees CI status on the PR, so a check that fails later is
  handled as a normal fix — no need to babysit the run.
- Don't commit, push, open PRs, **or merge** unless asked — **merge is always the human's call.**

## Referenced files

- Operating manual + Definition of Done: `AGENTS.md`
- Templates: `docs/` (context, `prd/0000-product.md`, prd, adr, architecture, contracts,
  security, briefs, progress, test-strategy, runbook)
- Custom skills: `feature-start`, `project-status`, `definition-of-done-review`
