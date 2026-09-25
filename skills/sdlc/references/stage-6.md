# Stage 6 — Review

Read this before any Stage 6 work. This stage is **proceed-with-disclosure**: review inline, fix
findings, continue. Review topology and security-review coverage live in `references/rules.md`.

## Mandatory reviews, in order

Run on a **clean materialization of the complete target-to-tree delta**, with evidence bound to
its target, parent, and tree:

1. `code-review` — correctness, readability, architecture, security, performance; severity-labeled
   findings and a verdict.
2. `code-simplification` — reduce unnecessary complexity in the candidate without changing
   behavior, preserving contracts, conventions, and verification requirements.
3. `definition-of-done-review` — local readiness against `AGENTS.md`'s Definition of Done, which
   this skill deliberately embeds no copy of. Its mechanical **stale-claim scan** is part of local
   readiness: check that no doc prose carries task or decision status that belongs to the tracker
   or ADRs, and that current-behavior claims match the change's evidence.

`security-review` is **mandatory** whenever a sensitive area is touched — before landing a
sensitive Stage 0/2 planning package and again on the implementation diff at this stage. Coverage
rules (intended file scope, reviewed identity, exclusions, blocking on incomplete coverage) are in
`references/rules.md` → Security-review coverage; the canonical sensitive-area list is
`AGENTS.md` → Sensitive areas.

## After review

Fix findings, rerun the affected review after substantive edits, and confirm the clean diff, local
DoD evidence, and pending CI state. Only then make the single combined push/PR ask of the CI seam
(`references/rules.md`) and continue to Stage 7.
