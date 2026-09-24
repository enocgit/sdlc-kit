---
name: code-review
description: >
  Reviews the complete target-to-tree diff across five axes — correctness, readability,
  architecture, security, and performance — with severity-labeled findings and a verdict. Use at
  Stage 6 before the Definition of Done check, during QA after implementation, or when the user
  asks to review a diff or "check my changes before merge".
---

# code-review

A maintained adaptation of Addy Osmani's `code-review-and-quality` skill, re-scoped from PR review
to the complete target-to-tree diff this pipeline reviews. Attribution and license live in
`NOTICE.md` and `LICENSE.txt`.

## The approval standard

Approve a change when it definitely improves overall code health, even if it isn't perfect. Don't
block a change because it isn't exactly how you would have written it. Do block a change that
introduces a defect, weakens an invariant, or makes structure worse.

## Scope

Review the complete target-to-tree delta on a clean materialization: changed lines with enough
surrounding context to judge them, plus every file the change adds, removes, or retypes. Do not
review unrelated code; do note when an unrelated area is load-bearing for the change.

Before reviewing, read the project's instruction and architecture docs for the touched area
(`AGENTS.md`, `docs/architecture.md`, relevant ADRs and contracts) so local patterns are
distinguished from defects.

## Kit integration

This pass is review-only. Run it against the complete clean materialization of the current
candidate; do not edit that materialization, commit, or perform landing actions. Report findings,
including confirmed candidate-owned dead code, to the parent or author. The parent or author may
apply accepted cleanup to the source candidate; after any such change, create a fresh materialization
and rerun the affected reviews. Uncertain findings are review notes, not a reason to block this pass.

## The five-axis review

### 1. Correctness

- Does the code do what the spec, task, or contract says it should?
- Are edge cases handled: empty, null, boundary values, concurrency, failure paths?
- Do tests cover the change's behavior, not its implementation details? Would they catch a
  regression? Verification must be proportional to risk: non-trivial executable behavior needs
  focused automated coverage, and bug fixes start from a failing test or reproducer.
- Are there off-by-one errors, race conditions, or state inconsistencies?

### 2. Readability

- Are names descriptive and consistent with project conventions?
- Is control flow straightforward — no nested ternaries, deep callbacks, or clever tricks?
- Are abstractions earning their complexity? Don't generalize until the third use case.
- Is a new conditional bolted onto an unrelated flow? That is a design smell, not a nit — push the
  logic into its own helper, state, or policy instead of tangling an existing path.
- Do repeated conditionals on the same shape appear? They signal a missing model or dispatcher; a
  "temporary" branch is usually permanent debt.

### 3. Architecture

- Does the change follow existing patterns or justify a new one? Are module boundaries and
  dependency directions preserved?
- Does a refactor reduce complexity or just relocate it? Count the concepts a reader must hold. If
  a "cleaner" version leaves that count unchanged, it isn't cleaner — prefer the restructuring that
  makes whole branches, modes, or layers disappear.
- Is feature-specific logic leaking into a shared or general-purpose module? Keep logic in its
  owning layer and reuse the existing canonical helper instead of a near-duplicate.
- Are type boundaries explicit? Question gratuitous `any`/`unknown`/casts and silent fallbacks that
  paper over an unclear invariant.

### 4. Security

Flag what this diff-level review can see; a sensitive-area change additionally requires the
separate `security-review` pass with full scoped coverage.

- Is external input validated at the boundary before use in logic or rendering?
- Are secrets kept out of code, logs, and version control?
- Are authentication and authorization checks present where the change adds or moves an entry
  point?
- Are queries parameterized, outputs encoded, and external data treated as untrusted?
- Are new dependencies from trusted sources, actively maintained, and license-compatible?

### 5. Performance

- N+1 query patterns, unbounded loops, or unconstrained data fetching?
- Synchronous operations that should be async; large objects built in hot paths?
- Missing pagination on list endpoints; repeated work that could be hoisted?

## Structural remedies

When you flag a structural problem, propose the move, not just the problem: replace a conditional
chain with a typed model or dispatcher, collapse duplicate branches, separate orchestration from
business logic, move feature logic to its owning module, reuse the canonical helper, delete a
pass-through wrapper, or extract a helper. Prefer the remedy that removes moving pieces over one
that spreads the same complexity around.

## Change sizing

Roughly 100 changed lines review well in one sitting; ~300 is acceptable as one logical change;
~1000 is too large — split it (stack, by file group, horizontal, or vertical slices). When a small
diff pushes an already-large file further past a healthy boundary, ask for decomposition before
piling on. Keep unrelated refactors out of scope. In this kit's inline Stage 6 workflow, review
findings and necessary cleanup for the current candidate stay in the same reviewed candidate and
follow the conductor's review, commit, and human-controlled landing rules. Complete file
deletions and mechanical refactors are acceptable at any size.

## Findings

Label every finding so the author knows what is required:

| Prefix | Meaning | Author action |
| --- | --- | --- |
| *(no prefix)* | Required change | Must address before merge |
| **Critical:** | Blocks merge | Security vulnerability, data loss, broken functionality |
| **Nit:** | Minor, optional | May ignore — formatting, style preference |
| **Consider:** | Suggestion | Worth weighing, not required |
| **FYI** | Informational | No action needed |

Order findings by leverage: correctness and security first, then structural regressions and missed
simplifications, then everything else. A few high-conviction comments beat a long list. Quantify
where possible. Do not soften real issues, and do not rubber-stamp.

**Presumptive blockers** — surface the simpler design for each; escalate to Required only when the
change actively makes structure worse: a refactor that relocates complexity; growth past a file's
healthy size without decomposition; feature logic in a shared module; a near-duplicate of a
canonical helper; a silent fallback hiding an unclear invariant.

## Dead code

After refactoring, list newly unreachable or unused elements explicitly. Report confirmed dead code
owned by the current candidate to the parent or author; do not remove it from the clean materialization.
When deadness, ownership, public API impact, or scope is uncertain, leave the element untouched,
record or escalate the uncertainty as a finding or review note, and continue the Stage 6 review. Do
not silently remove elements or refactor unrelated code.

## Verification of the review

- [ ] Context understood: what the change does, why, and against which spec or contract
- [ ] Tests reviewed before implementation; coverage proportional to risk
- [ ] All five axes walked for each changed file
- [ ] Every finding severity-labeled and ordered by leverage
- [ ] Author's verification story checked: what was run, what was shown
- [ ] Verdict stated: approve, or request changes with the required items listed
