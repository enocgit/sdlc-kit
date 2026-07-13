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

1. **Pick the task.** Confirm the GitHub issue # and slug with the user. One task per run.
2. **Isolate the workspace — default to a feature branch.** Create `feat/{issue#}-{slug}` directly.
   Only reach for an isolated **git worktree** (delegating to `using-git-worktrees` if installed)
   when isolation is genuinely critical — parallel work on multiple features, or disposable
   experiments — or when the user asks. Either way, FIRST run these guards (the worktree skill does
   them for you; the branch path must not skip them):
   - **Clean tree:** `git status --porcelain` is empty — nothing uncommitted to clobber.
   - **Fresh base:** check out the default branch and pull, so the feature branches off latest.
   - **Green baseline:** install deps and run the test suite once; if it's already red, stop and
     report — don't start work on a broken baseline.
   Then create `feat/{issue#}-{slug}`. One feature per workspace; don't touch other branches.
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
