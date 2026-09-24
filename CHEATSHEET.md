# SDLC cheatsheet

Use this during a run. `README.md` explains the kit; `templates/AGENTS.md` is the adopter manual
that installs as the project's `AGENTS.md`; the root `AGENTS.md` governs this maintainer repository.
The `sdlc` skill routes the work.

## Workflow

| # | Stage | Output | Gate or handling |
| --- | --- | --- | --- |
| 0 | Context + Foundation | filled context, product requirements document (PRD), test strategy, foundational ADRs, architecture/security, and core contract | fill context, then approve foundation |
| 1 | Spec | optional brief and feature PRD | approve PRD |
| 2 | Architecture + Contract | ADRs, architecture/security updates, and frozen contract | approve and freeze |
| 3 | Decompose | tracker tasks | disclose |
| 4 | Implement | one task on a `feat/*` branch | approve compact task plan |
| 5 | Quality assurance (QA) | tests, runtime or relevant non-runtime evidence, continuous integration (CI) | none |
| 6 | Review | clean diff and security review when required | inline; no separate gate |
| 7 | Land | pull request (PR) or direct-merge path | human merges |
| 8 | Retro | per-task learnings; after all feature tasks, reconcile feature artifacts, frozen contract, contract index, and parent-epic status | none |

A feature's parent tracker record, often called an epic, groups its child tasks. A fresh project has
six **hard pipeline gates** for a one-task feature: context, foundation, PRD,
architecture and contract, the task plan, and merge. Adoption combines the first two into one Stage 0
approval, so a one-task feature has five. Each additional task adds a task-plan approval and a merge
approval. Repository-action approvals and external-tracker write approvals are separate safety stops,
not extra pipeline gates. At other stages, work continues after decisions are disclosed. One approval
may cover commit, push, and PR creation when the request names all three. Merge always stays separate.

At Land, if hosting has no PR workflow, the agent pushes when a remote exists and runs available CI;
the human merges directly. With no remote, the human merges the local branch.

## Choose a path

- **Feature, user-facing, or risky:** Stages 1–8 after Stage 0.
- **Bug fix or small enhancement:** Implement → QA → Review → Land → Retro.
- **Chore, docs, or dependency update:** Implement → Review → Land → Retro.
- Use the full path when the change affects a contract, sensitive area, or recorded decision.

## Core rules

- **Foundation:** create project-wide context, test strategy, product requirements document (PRD),
  architecture decision records (ADRs), architecture, threat model, and core contract once. Create
  feature artifacts per feature.
- **Contract:** define and freeze the interface before implementation. Generate types or share
  contract-defined types directly. Regenerate generated types after contract changes; never
  hand-duplicate types. A shipped-contract change with a deployed consumer needs a versioning or
  deprecation ADR. If there is no deployed consumer, compatibility versioning may be deferred only
  with applicable approval: follow the [contract guide](./templates/docs/contracts/README.md), re-freeze
  the contract, and record the deferral in the [production register](./templates/docs/context.md) with
  its owner and first-deployed-consumer trigger.
- **Sensitive work:** use the canonical list in
  [`templates/AGENTS.md`](./templates/AGENTS.md#sensitive-areas). The agent updates `docs/security.md`
  and runs `security-review` before asking for approval to land sensitive Stage 0 or Stage 2 planning;
  review the implementation again at Stage 6.
- **Ambiguity:** stop and ask instead of guessing about PRDs, ADRs, or contracts.
- **Ready:** acceptance criteria are testable; the contract is frozen and matches its accepted ADR
  and the architecture update; open questions are closed.
  The task should fit in about one day.
- **Migrations:** use expand/contract (migrate → deploy → clean up) when a table has real data or
  any deployed reader/writer; direct changes are fine before then.
- **Done:** acceptance criteria pass; the contract is honored; proportional verification, reviews,
  architecture, ADRs, and tracker updates are complete.
- **CI:** available continuous integration (CI) must be green. Unreachable CI blocks; it does not
  exempt the change.

## Git and trackers

- Keep `main` deployable. Use short-lived `feat/{id}-{slug}` branches.
- Use imperative Conventional Commits: `type(scope): summary`, at most 72 characters.
- Use `Refs #N` or `Closes #N` for GitHub when the change completes an existing issue; never create
  an issue just to have one to reference. Use native keys for other trackers and no issue syntax for
  local-only IDs.
- Land Stage 1–2 planning artifacts once after Stage 2, before branching; Stage 0 artifacts may land
  after their gate. With a remote, an unprotected `main` takes the commit and push under one
  approval; a protected `main` takes a `plan/*` PR first.
- Keep commits and PRs focused. The human performs every landing merge.
- On GitHub, `Closes #N` closes the referenced issue when the PR merges. With a native external
  integration, verify that it closed the task after merge; if closure did not occur, ask for approval
  for the post-merge transition. Without Git integration, ask for approval and close the external task
  after merge confirmation. In local-only mode, update `docs/progress.md` after merge.

## Artifacts

| Artifact | Location |
| --- | --- |
| Domain context and learnings | `docs/context.md` |
| Product and feature PRDs | `docs/prd/` |
| Decisions | `docs/adr/` |
| Current system shape | `docs/architecture.md` |
| Integration truth | contract source named in `docs/contracts/README.md` |
| Threat model | `docs/security.md` |
| Test policy | `docs/test-strategy.md` |
| Task status | external tracker, or `docs/progress.md` in local-only mode |

The optional `improve` skill audits a completed epic. It writes plans under `plans/`, stays outside the
pipeline, and is offered only after all tasks in the epic are complete, not after a single task. For
`improve next`, decline its planning step and start `sdlc {chosen direction}` at Stage 1. `address-review`
triages comments on an open PR before fixing, refuting, or deferring them.
