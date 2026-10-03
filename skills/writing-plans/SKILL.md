---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

A maintained adaptation of Jesse Vincent's `writing-plans` skill from
[obra/superpowers](https://github.com/obra/superpowers) (MIT — see `LICENSE` in this directory).
The decomposition method is kept; the outputs and hand-offs are re-scoped for this kit's Stage 3,
as stated in the body below.
# Writing Plans

## Overview

Write implementation plans for an executor with repo access and real skill, but zero context on this feature. The plan carries what the executor cannot reconstruct: exact file paths, the interfaces between tasks, the verification command with its expected outcome, STOP conditions, and global constraints verbatim. Do not narrate the executor's mechanics — no inline test source, no keystroke choreography, no expected error strings; the executor writes its own code and tests. DRY. YAGNI. TDD. Frequent commits.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Output:** the breakdown goes where Stage 3 says — tracker issues (GitHub by default),
`docs/progress.md` rows when the project is local-only, or an audit plan backlog under
`docs/plans/`. The task and plan formats below apply to whichever record the project uses; when
the record is tracker issues, each task becomes an issue body following the project's epic/task
issue templates.

**Workspace:** none here — Stage 4's `feature-start` isolates the workspace when a task starts
(direct feature branch by default; a git worktree only as the explicit manual escape hatch).

## Scope Check

If the PRD covers multiple independent subsystems, it should have been broken into separate PRDs during Stage 1. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle and is worth a
fresh reviewer's gate. When drawing task boundaries: fold setup,
configuration, scaffolding, and documentation steps into the task whose
deliverable needs them; split only where a reviewer could meaningfully
reject one task while approving its neighbor. Each task ends with an
independently testable deliverable.

## Parallel groups

Declare groups of tasks that may execute simultaneously: disjoint file sets, no `Consumes` on an
incomplete task, no shared tracker row. Name each group in the plan ("tasks 3, 4, 7 — one
parallel group"); everything else runs serially. Contested or unclear → serial.

## Commit cadence

Each task ends in its own commit; the commit precedes QA and review. Thin slices of one
shippable change may share a branch and land as one reviewed merge; independently shippable
tasks land task-by-task through their own Stage 6–7 cycle.

## Plan Document Header

**Every plan document (backlog mode) MUST start with this header:**

```markdown
# [Feature or Audit] Implementation Plan

> **Executor instructions:** read the full plan, run each verification command, honor the STOP
> conditions, and update this plan's status row when done. Workspace isolation, commits, and
> parallel-group execution are owned by Stage 4, not by this plan.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**PRD:** [path to the PRD this plan implements — the plan argues from the PRD, so it travels
with it; executors read both]

## Global Constraints

[The PRD's project-wide requirements — version floors, dependency limits,
naming and copy rules, platform requirements — one line each, with exact
values copied verbatim from the PRD. Every task's requirements implicitly
include this section.]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, parameter
  and return types. A task's implementer sees only its own task; this
  block is how it learns the names and types neighboring tasks use.]

**Verification:** [the exact command(s) and the expected outcome — the failing check for a bug
fix or non-trivial behavior, then the passing state; name the observed failure a RED run should
produce. One task, one verification block — no choreography.]

**STOP when:** [states that abort the task — a red baseline unrelated to the planned RED, the
drift check failing, the frozen contract not matching the plan's premise]

**Close out:** disclose completion and update the tracker record per the project's tracker
rules (the task stays _in review_ until the human merges at Stage 7).
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without the exact check and its expected outcome)
- "Similar to Task N" (repeat the content — the executor may read tasks out of order)
- Steps that name a check without its exact command and expected outcome
- References to types, functions, or methods not defined in any task

## Self-Review

After writing the complete plan, look at the PRD with fresh eyes and check the plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. PRD coverage:** Skim each section/requirement in the PRD. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a PRD requirement with no task, add the task.

## After the Breakdown

Report the breakdown to the conductor — the epic, its tasks in build order, the declared
parallel groups, and where the record lives. Stage 3 discloses and continues; execution starts
at Stage 4 via `feature-start`. Do not dispatch executors from here: task isolation,
parallel-group execution, fresh-context review, and the merge gate are owned by the pipeline
stages, not by this skill.
