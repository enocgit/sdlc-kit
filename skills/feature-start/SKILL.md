---
name: feature-start
description: >
  Starts implementation of one decomposed task: isolates a workspace (a feature branch by default;
  a git worktree only when isolation is critical), loads the relevant PRD, ADR, and frozen contract
  into context, then enters plan mode and proposes a per-task plan for approval before any code is
  written. Use at the start of Stage 4 (Implement) once scope is approved, or when the user says
  "start working on issue #N",
  "begin this task", or "let's implement {feature}".
---

# feature-start

Prepare a clean, well-contextualized starting point for implementing one task, then stop for a
plan approval gate.

## Steps

1. **Pick the task.** Confirm the task's **identifier and slug** with the user. The identifier is
   the GitHub issue number by default; on another tracker its key (`ENG-123`); in **local-only**
   mode the `#` column of the task table in `docs/progress.md`. Never invent one. One task per run.
2. **Isolate the workspace — default to a feature branch.** Create `feat/{id}-{slug}` directly.
   Only reach for an isolated **git worktree** (delegating to `using-git-worktrees` if installed)
   when isolation is genuinely critical — parallel work on multiple features, or disposable
   experiments — or when the user asks. Either way, FIRST run these guards (the worktree skill does
   them for you; the branch path must not skip them):
   - **Clean tree:** `git status --porcelain` is empty — nothing uncommitted to clobber. If the
     *only* change is the local-only tracker (`docs/progress.md`) that Decompose just wrote, ask to
     commit it and continue once approved — this is the gate that clears it. If the default branch
     is PR-protected, a direct commit there can never be pushed: land it via a `plan/{NNNN}-{slug}`
     branch → PR → merge first, same as any other planning commit (`AGENTS.md` → Where planning
     commits land), then branch `feat/*` from the updated default branch. Anything else: stop.
   - **Fresh base:** check out the default branch and bring it up to date before branching — a
     stale base is as bad as a dirty tree. With an upstream (`git rev-parse --abbrev-ref
     '@{upstream}'` succeeds), `git pull`. **With a remote but no upstream** — before the first
     push, or after tracking was removed — don't assume local is current. First resolve *which*
     remote is authoritative: exactly one → use it; several (`origin` plus a fork or mirror) →
     **ask which owns the default branch**, never guess, since fast-forwarding from a fork bases
     the work on the wrong history. Then `git fetch` that remote and fast-forward onto its
     `{default}`, which may have advanced. **Only a repo with no remote at all is latest by
     definition.** If the remote is unreachable (offline, expired auth), don't declare local fresh —
     fast-forward onto its cached remote-tracking ref if that is ahead, and if freshness still can't
     be verified, say so and let the human choose rather than branching from a maybe-stale base
     (auth the cause? surface the one-time fix — `AGENTS.md` → Guardrails). Never fail the guard
     over a missing upstream.
   - **Green baseline:** install deps and run the test suite once; if it's already red, stop and
     report — don't start work on a broken baseline.
   Then create `feat/{id}-{slug}` using the identifier from step 1. One feature per workspace;
   don't touch other branches.
3. **Load context.** Read into context:
   - `docs/context.md` (domain, glossary, hard constraints — incl. retro learnings from prior cycles)
   - The feature's PRD in `docs/prd/`
   - Any ADR(s) it depends on in `docs/adr/`
   - The frozen contract artifact (OpenAPI/tRPC/schema) the task implements against
   - `docs/test-strategy.md` (Definition of Done + which layer to test at)
4. **Plan.** Enter plan mode. Produce a granular plan (small steps, exact file paths, the tests
   you'll write first). Hand off to `executing-plans` / `test-driven-development` for execution.
5. **GATE.** Present the plan. Ask for approval before writing any code.

## Rules

- Implement strictly against the frozen contract. If you discover the contract is wrong, STOP
  and raise it — a contract change is a decision (new/updated ADR), not an inline edit.
- If the task is bigger than ~a day of work, propose splitting it before starting.
- **Keep the SDLC status header** on every user-facing message, just like the conductor — open with
  `SDLC ▸ Stage 4/8 Implement · task #N · {next: plan approval / …}`. You're inside the pipeline even
  though `sdlc` isn't the active skill; don't drop the header once implementation starts.
- Don't commit or push unless asked.
