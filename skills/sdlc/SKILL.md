---
name: sdlc
description: >
  Runs the project's gated delivery workflow end to end: foundation, plan, decompose, build,
  review, land, and retro, with human approval at each gate and the human performing every merge.
  Use when the user wants to build a feature or fix "the disciplined way", start or resume
  structured work, asks "what stage are we at" or "what's next", or says "start the sdlc".
---

# sdlc

You run the workflow defined in the project's `AGENTS.md`. This skill adds the per-stage detail.
`AGENTS.md` wins any conflict. Read `AGENTS.md`, `docs/context.md`, and `docs/test-strategy.md`
before acting. Landing, tracker, and amendment mechanics are in `references/rules.md`; read it
before any landing or tracker write.

## Orient

1. Infer the stage from the artifacts: unfilled templates mean Stage 0; an approved change proposal
   with no tasks means Stage 2; open tasks mean Stage 3; and so on. Read the tracker that
   `docs/context.md` → Lifecycle names, or the proposal's task checklist when it names none.
2. Pick the path: feature (Stages 1–6), bug fix or chore (Stages 3–6). A contract change, a
   trust-boundary change, or a new decision moves small work to Stage 1. When unsure, ask.
3. If the repository contradicts `docs/context.md` → Lifecycle (a production deploy workflow while it
   says no traffic, a migration on real data while it says none), flag it and ask for the update.
4. State the path, stage, and next action, then act.

Use bundled skills when the harness can invoke them; otherwise apply the procedure below by hand.

## Stage 0 — Foundation

Stage 0 is incomplete while any `STATUS: TEMPLATE` marker or `{placeholder}` remains in
`AGENTS.md` or `docs/`, outside files named `TEMPLATE.md`.

- **New project:** fill `docs/context.md` (product, Lifecycle, outside consumers, hard
  constraints), set the stack and check command in `AGENTS.md`, set `docs/test-strategy.md`, and
  write only the ADRs a first feature cannot start without. Describe only what exists: with no code
  yet, `docs/architecture.md` records the scaffold, `docs/specs/README.md` lists areas without links
  until their spec exists, and `docs/security.md` claims only controls in place. Planned shape goes
  in the first change proposal. Write no product code; the checks need one trivial module and test.
- **Existing codebase:** reconstruct the same set read-only from the code. Write specs for the
  areas that exist, backfill ADRs only for hard-to-reverse choices already made, and fold any
  existing PRDs into specs. `improve-codebase-architecture` can supply the reading heuristics.
- **Prove the checks.** Plant one type error, run `{check command}`, see it fail at the typecheck,
  and revert; repeat for one failing test and one lint violation. One plant per run: a chained
  command stops at its first failure. Only the check command's output counts, not editor or harness
  diagnostics. Then see CI fail on one plant. With no remote, CI is unproven: say so at the gate and
  add it to the production register with the trigger "first push". A check that cannot fail is not
  a check.

**Gate: approve foundation.** Then land it per `references/rules.md` → Landing.

## Stage 1 — Plan

1. Interview with `grilling` until no open question remains: one round at a time, each question
   with your recommended answer. No code.
2. Write `docs/changes/NNNN-{slug}.md` from its template: why, the spec delta (requirements added,
   changed, or removed, with IDs), acceptance criteria, approach, contract impact, and risks. Stay
   within its budget.
3. Write an ADR only for a choice that is hard to reverse or constrains later work.
4. Freeze a contract only when `docs/context.md` lists an outside consumer that cannot change in
   the same PR. Interfaces used only inside this repo stay unfrozen and covered by tests.
5. When the plan changes a trust boundary, put the threat delta in the proposal and run
   `security-review` on the proposal before the gate.

**Gate: approve plan.** Landing follows team shape (`references/rules.md` → Landing).

## Stage 2 — Decompose

Split the change into vertical slices, each one PR a reviewer can read in one sitting: one behavior
end to end with its tests, usually under ~300 changed lines. Each task states its acceptance criteria
(citing requirement IDs), the test layer for each behavior, its dependencies, and the files it
likely touches. Write tasks to the tracker (`references/rules.md` → Tracker); a one-task change needs
no epic.

Declare parallel groups only for tasks with disjoint files and satisfied dependencies; everything
else runs serially. Disclose the breakdown and continue.

## Stage 3 — Build

1. Start from a clean, up-to-date default branch and create `feat/{id}-{slug}`. Never force a
   checkout or overwrite uncommitted work; stop and ask instead. Run declared parallel tasks in
   separate worktrees when the harness supports them.
2. Load the proposal, the specs it touches, the relevant ADRs, and any frozen contract.
3. Disclose a short plan. Stop for approval only when the task is sensitive (`AGENTS.md` →
   Sensitive changes) or deviates from the approved decomposition.
4. Test first. For each behavior, write the test at the assigned layer, citing its requirement ID,
   watch it fail for the right reason, then implement. Bug fixes use `diagnosing-bugs`: reproduce
   first, fix at the root cause.
5. UI work: use `frontend-design`, and exercise the change in a real browser with the harness's
   browser tool, or `webapp-testing` when the harness has none. Backend work: verify at the API or integration level.
6. Update the spec, architecture, and contract index for the behavior this task ships, in the same
   commit. Run the check command for the touched packages; CI is the merge gate.
7. Commit the task. Bug fixes and chores with no plan still get a test and a reviewer.

## Stage 4 — Review

Review in a context that did not write the change: a fresh subagent, a separate session, or a human.
This skill authorizes spawning that reviewer. Give it the diff against the target branch, the
proposal, the touched specs, and any contract: raw artifacts, never your summary of them.

- `code-review` on every change.
- `security-review` when the change is sensitive; it writes the security record.
- Fix required findings as follow-up commits. Re-review only fixes that change behavior.
- Weigh hardening findings against the Lifecycle block; defer what absent traffic would need to the
  production register.
- If a third round still finds required changes, stop and ask the human whether the design needs
  another look.

Then push the branch and open the PR (no ask needed). Disclose the review outcome.

## Stage 5 — Land

Fill the PR template, including "Where to look". Use `Closes #N` only on GitHub and only for an
existing issue. Report in one line (PR link, CI running) and stop; do not poll CI. The human merges.
Without a PR workflow, follow `references/rules.md` → Landing.

`SDLC ▸ Stage 5/6 Land · next gate: merge when CI is green`

## Stage 6 — Retro

After the merge, switch to the synced default branch.

1. **Close the loop.** Confirm the tracker moved (`references/rules.md` → Tracker). When the last
   task of a change lands, check that specs, architecture, contracts, and `docs/security.md` match
   what shipped, then mark the proposal Shipped with links to its merges. If the change gives the
   product its first deployed consumer, real data, or traffic, propose the Lifecycle update.
2. **Learnings.** Add one only if a future agent would do the wrong thing without it: 0–3 dated
   bullets in `docs/context.md`, each at most three lines. If the "learning" is a bug in the
   project, fix the bug instead. Prune fixed or covered bullets; promote a bullet that applies across
   features into `AGENTS.md`, `docs/test-strategy.md`, or an ADR. Keep at most 30.
3. Land any edits per `references/rules.md` → Landing. An empty retro lands nothing.

Next feature: return to Stage 1. After a large change, offer an `improve-codebase-architecture`
pass; its findings enter as a new change proposal.
