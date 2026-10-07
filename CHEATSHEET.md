# SDLC cheatsheet

Use this during a run. `templates/AGENTS.md` is the adopter manual installed as the project's
`AGENTS.md`; the `sdlc` skill holds the per-stage detail.

## Workflow

| # | Stage | Output | Stop |
| --- | --- | --- | --- |
| 0 | Foundation | context and lifecycle, spec skeleton, foundational ADRs, proven check command | approve foundation |
| 1 | Plan | change proposal (`docs/changes/`), ADRs, frozen contract when needed | approve plan |
| 2 | Decompose | tasks with acceptance criteria and test layers | disclose |
| 3 | Build | one tested, committed task with specs updated | disclose; gate on a trust-boundary change or plan deviation |
| 4 | Review | fresh-context `code-review`; `security-review` when sensitive | disclose |
| 5 | Land | PR with "Where to look" | the human merges |
| 6 | Retro | specs match what shipped; 0–3 learnings | disclose |

Bug fix or chore: Stages 3–6. A contract, trust-boundary, or decision change: back to Stage 1.

Task commits, `feat/*` pushes, and opening a PR need no ask. Writing the default branch, an external
tracker, or a new remote does.

## No-compromise rules

1. A human performs every merge.
2. Review runs in a context that did not write the change.
3. A trust-boundary change gets a security review before merge.
4. Implementation never drifts from a frozen contract.
5. Behavior ships with tests, and each check is proven able to fail.
6. The spec states what actually shipped.
7. No secrets in the repository, logs, or artifacts.

## Where things live

| What | Where |
| --- | --- |
| Current behavior | `docs/specs/{area}.md` |
| Proposed change | `docs/changes/NNNN-{slug}.md` |
| Hard-to-reverse decisions | `docs/adr/` |
| System shape | `docs/architecture.md` |
| Contracts | in code; indexed in `docs/contracts/README.md` |
| Trust boundaries and review records | `docs/security.md`, `docs/security/records/` |
| Test layers | `docs/test-strategy.md` |
| Lifecycle, register, learnings | `docs/context.md` |
| Task state | tracker, or the proposal's task list |

## Budgets

Change proposal ~80 lines · ADR ~60 · security record ~40 · issue ~15 · `context.md` ~120 with at most
30 learnings.

## Tests

- Unit tests for logic with many cases; integration tests against real infrastructure for wiring;
  a few end-to-end tests for critical journeys.
- Each new test is seen failing first. Test names cite requirement IDs.
- Pull requests run affected packages; the push to the default branch runs everything; no run repeats
  the same work.

## Git and trackers

- Branches: `feat/{id}-{slug}`. Commits: `type(scope): summary`, ≤72 chars, no agent attribution.
- `Closes #N` is GitHub-only. Other trackers use their own integration or a post-merge update with
  an ask.
- Solo projects land the proposal with the first task's PR; team projects land it on `main` first.
