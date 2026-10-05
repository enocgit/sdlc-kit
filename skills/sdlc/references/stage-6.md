# Stage 6 — Review

Read this before any Stage 6 work. This stage is **proceed-with-disclosure**: review, fix
findings, continue. The CI seam and security-coverage musts are restated below; the full review-
topology machinery stays in `references/rules.md` (canonical).

## Fresh context first

**Reviews must not share context with implementation.** The author of a change — the agent that
wrote it — reviews it with the same blind spots that produced it, and self-review in the same
session reliably under-detects. Where the runtime allows it, run these reviews in a context that
did not implement the change: a fresh subagent, a separate session, or an external reviewer.
**This mandate is standing operator authorization** for spawning fresh-context review
subagents or lanes — a runtime's default deference-to-operator rule does not override it. Where
the runtime truly has no such mechanism, name the substitute you used (a clean re-read of only
the diff and its contract, with implementation context flushed) and why — never silently
self-review, and name the substitute in the Land report.

When a reviewer lacks shell/git access, the implementer materializes what it cannot — committed
ranges, blob hashes, evidence transcripts — as **raw artifacts**. Never hand a reviewer a narrative
account of the change, the review history, or the findings so far: the reviewer's judgment forms
on the evidence, not the implementer's summary of it. Answering a reviewer's context request means
pointing at the artifact, not writing the story.

## Mandatory reviews, in order

Run on a **clean materialization of the complete target-to-tree delta**, with evidence bound to
its target, parent, and tree, in a fresh context (above):

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
musts, restated (`references/rules.md` → Security-review coverage is canonical): establish the
intended file scope before invoking the tool (PRD, ADRs, contracts, threat model, implementation,
tests — including staged, unstaged, and untracked files); compare the tool's actual coverage with
that scope; read omitted files directly and review them by the structured manual procedure in
`references/rules.md`; a committed-only scope resolver under-counts an uncommitted delta, so there
its report is not authoritative and the manual review establishes coverage; exclusions cannot waive
relevant sensitive changes; if required content is
inaccessible or coverage is unknown, report incomplete coverage and **block** rather than return a
clean verdict. Record coverage and limits in a dated record under `docs/security/records/` and
index it in `docs/security.md`. When several plans share one working tree, scope each review to its
own plan's delta and name co-resident changes — including copies in other worktrees and stashes —
with the coverage that owns each. The canonical sensitive-area list is `AGENTS.md` → Sensitive areas.

**Re-review after substantive fixes.** Fixes from a review round that change behavior require
another fresh-context review scoped to the fixes (and whatever they touch) — the fix author's own
test pass does not retire findings. Stop when a round returns only advisory findings; do not loop
for stylistic residue.

## The CI seam (end of this stage)

Task commits and review fixes are already in — this stage ends in pushes, not asks: push the
`feat/*` branch and open the PR where hosting supports it, then stop; the merge is the gate
(`references/rules.md` → The CI seam). No ask is needed for the push or PR. Before pushing,
verify the final commit's parent and tree, and rerun every metadata- or topology-dependent check
against it — a security record's reviewed-subject identities
included.

No CI workflow → CI is N/A; a
workflow configured but blocked is a blocker (rules.md → capabilities), and a merge over it says so
in the PR body or security record; a workflow configured with no remote is dormant — merge locally,
then require green on the first push before any further merge.

## After review

Fix findings as follow-up commits on the same branch, rerun the affected review after substantive
edits, and confirm the clean diff, local DoD evidence, and pending CI state. Then push per the
CI seam above and continue to Stage 7.

## Next

After this stage's gate approval or proceed-disclosure, announce Stage 7 and read
`references/stage-7.md` before acting on it — the skill alone is not the procedure.
