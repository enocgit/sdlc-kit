# Stage 4 — Implement

Read this before any Stage 4 work. The verification rules this stage acts on are restated below
(`references/rules.md` stays canonical); the operating standard in `AGENTS.md`.

## Per task

1. `feature-start` isolates the workspace — direct feature branch by default; a git worktree only
   as the explicit manual escape hatch for parallel or disposable work (the operator supplies and
   verifies a private, new or empty path outside every checkout; use `feature-start`'s generic
   Git-only guidance; the kit does not enforce platform-specific path safety).
2. Load the relevant PRD, ADRs, and frozen contract slice.
3. Produce a **compact in-session plan** and disclose it, then implement. The plan is a gate only
   when the task touches a **sensitive area** (canonical list: `AGENTS.md` → Sensitive areas) or
   the plan **deviates from the approved decomposition** — in those cases stop for approval.
   Otherwise state the plan and proceed; the human can interrupt at any time.
4. One feature in flight per branch. Run the plan's tasks in its declared order: one parallel
   group at a time — tasks the plan declared parallel run in isolated worktrees (one per task,
   the operator-supplied escape-hatch recipe above), then verify the group together and commit in
   the plan's build order. Undeclared tasks run serially. Reference the tracker issue (its
   `#`/key) in commits/PRs when the task has one.

**Landing cadence is a plan property — set it here and disclose it.** Thin slices of one
shippable change can share a branch and land as one reviewed merge (several small commits, one
per referenced task); independently shippable tasks land task-by-task through their own
Stage 6–7 cycle. Cheap local merges favor per-task cadence; remote PR ceremony favors per-branch.
Whichever cadence the plan sets, the merge closes every task its cadence covers.

## Skills

- `feature-start` — workspace, context load, compact plan.
- `frontend-design` — UI work only.
- `ponytail` — backend/domain logic, parsers, transformations, state, tooling, and dependency
  choices. It cannot override contracts, security, accessibility, explicit requirements, or
  proportional verification; its one-check rule is a minimum, never a cap.
- `diagnosing-bugs` — bug-fix tasks: build a tight, red-capable feedback loop and minimise the
  repro before hypothesizing; fix at a correct seam under this stage's failing-test rule, and
  route a missing seam to the approach gate or an ADR.

## Definition of Ready (before implementing a task)

Acceptance criteria written and testable; the applicable contract frozen or explicitly N/A for
fast-path work with no integration contract; the frozen contract matching its accepted ADR and the
`docs/architecture.md` update; no open questions. Full list: `AGENTS.md` → Definition of Ready.

## While implementing

- **Verification in force:** the smallest local check that proves the change — a bug fix starts
  from a failing automated test or observable reproducer; non-trivial executable behavior
  (validation, authorization or security denial, error, retry, timeout, partial-failure branches)
  gets focused automated coverage, RED → GREEN; shared paths, contracts, and sensitive areas
  broaden coverage to all impacted packages. A full-suite run is never the local default.
- Never let implementation drift from the frozen contract.
- Keep the relevant doc (`architecture.md` / ADR) updated as you go; task status lives in the
  tracker, never in doc prose.
- After the commit, verify its parent and tree, and rerun every metadata- or topology-dependent
  check against that commit before relying on it.
- **Each task ends in its commit** — the commit precedes QA and review, and fixes found there
  land as follow-up commits on the same branch. Commits need no ask; pushes and PR openings need
  no ask; the merge is the stop (the CI seam, `references/rules.md`).

## Next

After this stage's gate approval or proceed-disclosure, announce Stage 5 and read
`references/stage-5.md` before acting on it — the skill alone is not the procedure.
