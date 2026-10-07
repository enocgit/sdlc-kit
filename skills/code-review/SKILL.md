---
name: code-review
description: >
  Fresh-context review of a change before merge: correctness, simplicity, structure, security, and
  readiness against the project's Definition of Done, with severity-labelled findings and a
  verdict. Use at the workflow's Review stage, or when the user asks to review a diff or "check
  my changes before merge".
---

# code-review

Review-only: report findings to the author; do not edit, commit, or land.

## Inputs

Review the committed diff against the target branch (`git diff {target}...HEAD`) on a clean tree,
plus every file it adds or removes. Read the change proposal, the specs it touches, relevant ADRs,
and any frozen contract. Do not accept the author's summary in place of these artifacts.

## The approval standard

Approve a change that clearly improves the codebase, even if you would have written it differently.
Block a change that introduces a defect, weakens an invariant, or makes the structure worse.

## Walk the change

1. **Correctness.** Does it do what the spec and acceptance criteria say? Edge cases: empty, null,
   boundaries, concurrency, failure paths. Do the tests prove behavior rather than implementation,
   and would they fail on a regression? Is each test at the layer `docs/test-strategy.md` assigns?
2. **Simplicity.** Is there a smaller design: reuse of an existing helper, the standard library, or
   an installed dependency; fewer branches, modes, or layers? A refactor that moves complexity
   without removing it is not a simplification. Name the simpler design; do not just say "simplify".
3. **Structure.** Feature logic in its owning module; no near-duplicate of a canonical helper; no
   silent fallback hiding an unclear invariant; no unrelated conditional bolted onto a shared flow.
4. **Security.** Input validated at the boundary; secrets out of code and logs; authorization on
   every new entry point; queries parameterized; new dependencies trustworthy. A trust-boundary
   change also needs `security-review`.
5. **Performance.** N+1 queries, unbounded loops or fetches, missing pagination, work repeated in a
   hot path.

## Readiness

Read the Definition of Done in the project's `AGENTS.md` and check the change against that exact
list. Then:

- **Acceptance criteria:** map each one to the test or observation that proves it.
- **Checks can fail:** a new test was seen failing first; a new or changed check command fails on a
  planted error.
- **Docs match the code:** specs, architecture, and contract index describe the shipped behavior.
  Run a stale-claim scan over changed docs *and source comments that carry current-behavior claims*
  (contract docblocks, module docstrings): search for `TODO`, `PENDING`, `Planned`, `In progress`,
  `Partially implemented`, and template markers. Each hit is deleted, moved to the tracker, or
  backed by evidence from this change.
- **Budgets:** count changed artifacts against `AGENTS.md` → Writing standard (`wc -l`).
- **Size:** about 300 changed lines reviews well; past about 1,000, ask whether it should be split.

## Findings

| Label | Meaning |
| --- | --- |
| **Critical:** | Blocks merge: security hole, data loss, broken behavior |
| *(none)* | Required before merge |
| **Consider:** | The author decides |
| **Nit:** | Optional |

Order by leverage, correctness and security first. A few high-conviction findings beat a long list.
Each finding names the location, the problem, and the fix. Weigh hardening findings against the
Lifecycle block in `docs/context.md`: hardening for traffic or data that does not exist yet is a
**Consider:** with a production-register entry, not a required change.

End with a verdict: **approve**, or **request changes** listing the required items.
