# Rules — cross-stage mechanics

The single source for mechanics that span stages. Stage references point here instead of
restating; `AGENTS.md` owns reader-facing standards and wins any conflict.

## Tracker and landing capabilities

**Tracker, remote, PR workflow, and CI workflow are independent capabilities.** _Local-only_ means
`docs/progress.md` replaces an **external tracker** — it does **not** imply there's no remote, and
such a project can still open PRs and run CI. A remote does **not** imply a PR workflow: a bare,
self-hosted, or backup remote has no PRs, branch protection, or checks. Decide on what the hosting
_actually supports_, never on remote presence as a proxy:

- **PR workflow available** → open the PR; run CI there when a CI workflow also exists; the human
  merges through the PR. No CI workflow → the CI check is N/A.
- **No PR workflow, CI workflow available** → push the branch to start CI, require green, then the
  human merges `feat/*` into `main` directly. **No remote** → CI is dormant, not N/A: merge locally
  per the row below, and the first push must produce a green run before any further merge.
- **No PR or CI workflow** → the human merges directly; push only if a remote exists.
- **A configured PR or CI workflow is unreachable** (expired auth, network, spending limit) → a
  **blocker, not a mode**: required checks and branch protection must not be routed around. Surface
  the fix (`gh auth setup-git`; `AGENTS.md` → Guardrails) and stop. Never invent a remote to satisfy
  the flow. If the human merges over the blocker, the merge names the state — the PR body or
  security record says the gate did not run and local verification was accepted in its place: an
  unverified gate, not a passing one.
- **The tracker follows capability the same way:** a remote appearing after a local-only
  decomposition migrates the tracker at the next task boundary — issues for unstarted tasks, issue
  numbers as task identity, `docs/progress.md` deleted in a landing commit naming the new tracker.
  Decide on what the hosting supports, never on issue absence (`stage-3.md` owns the procedure).

## Default-branch landings (Stage 0, Stage 2, Stage 8)

Planning packages and Retro edits land on the default branch, never a feature branch, and the ref
Stage 4 cuts from must already hold them. Stage 0 artifacts may land after the foundation gate; for
a feature, the Stage 1–2 package lands once after Stage 2; Stage 8 learnings land before the next
task or feature branch; final reconciliation waits for the last child. Ask for the landing action
by remote state:

- **No remote** → commit to the local default branch.
- **Remote, default branch unprotected** → commit and push it under the same approval, so the
  shared default branch holds the frozen contract. A commit alone leaves Stage 4 branching from a
  base the remote lacks, folding the planning package into the feature PR.
- **Remote, default branch protected** → `plan/{NNNN}-{slug}` → PR → merge, then branch `feat/*`;
  wait for the human to confirm the package reached the default branch.

Stage 4 branches from that clean ref; the branch carries the task implementation plus its required
task-scoped tests and docs (`AGENTS.md` → Where planning commits land).

**Complete what the ask named.** Before reporting a landing landed, verify every artifact the gate
ask named is in the commit. If one was omitted, commit and push it under the same approval — the
approval covered the package, not the omission — and say so in the report.

## Task completion by tracker

**`Closes #N` is GitHub-only syntax.** On Linear/Jira it either fails to close the real task or
closes an unrelated repo issue of that number — unless _that tracker's own_ Git integration is
configured, which auto-closes via its native key (`ENG-123`, `PROJ-45`), same mechanism, different
syntax. A **local-only** id is a `docs/progress.md` row, not an issue at all.

- **GitHub** — the PR carries `Closes #N` (only when the change completes a pre-existing issue),
  the issue stays **open** through Land, and merging closes it. Never close it by hand.
- **Linear/Jira with Git integration configured** — reference the native key per that integration's
  convention (commit/PR title or branch name); confirm the integration is actually wired before
  relying on it.
- **Linear/Jira with no Git integration, or local-only** — **no closing keyword anywhere**, in the
  PR or in commits. The task moves to _in review_ at Land and completes only after the merge.

**Who writes the tracker.** Against an external tracker `project-status` is read-only — it never
edits issues unless the user explicitly asks; a Linear/Jira transition is a separate,
outward-facing action: show the change and get a go-ahead before writing. In **local-only**,
`docs/progress.md` _is_ the tracker and `project-status` maintains it (its one documented write);
that edit rides its task's commit. A transition is never a silent side effect of opening
the PR — if it hasn't happened, report the tracker as stale rather than describing it as moved.

**After the merge — close the loop before Retro.** **GitHub** has closed the issue itself — nothing
to do. **Linear/Jira with Git integration** — verify it actually fired, don't assume. An
**alternate tracker with no Git integration** needs its task closed explicitly now — outward-facing,
so confirm before writing. **Local-only** needs the `docs/progress.md` row moved to `Done` — and
that file _is_ the tracker, so **check out the default branch and sync it first** (committing on the
just-merged `feat/*` strands the update on a dead branch while `main` reads _In review_). Then edit
and land it by remote state (Default-branch landings); Stage 8's learnings may ride the same commit.

## The CI seam (end of Stage 6, before Stage 7)

Task commits, `feat/*` pushes, and PR openings are **not asks** — Stage 4 commits per task, Stage 6
pushes and opens the PR without approval, and the merge is the gate. Before the push, verify the
final commit's parent and tree, and rerun every metadata- or topology-dependent check against it;
if any fails, stop before the push.

- PR workflow → open the PR; CI runs there; the human merges.
- Remote, no PR workflow → push the branch to start CI, require green, and the human merges
  `feat/*` into the default branch directly.
- **No remote** → the merge itself is the ask: "Approve commit and merge to the local default
  branch?" — **one combined stop**: the approval covers the commit that precedes the merge, so
  local-only work stops once, not twice. The human still owns the merge decision; record it in the
  tracker close-out.

The ask is the sentence above plus at most a one-line summary of what ships — commit lists,
PR descriptions, and CI status belong in the disclosure after the fact, not the ask.

No CI workflow → CI is N/A.

## Verification

`AGENTS.md` owns the standard; this maps it to stages. Every task needs proportional verification,
not necessarily a new test — name the smallest local check that proves the change:

- **Bug fixes:** start with a failing automated test or observable reproducer appropriate to the
  risk. **Non-trivial executable behavior** (validation, authorization or security denial, error,
  retry, timeout, partial-failure branches): focused automated coverage, RED → GREEN.
- **Docs:** link or rendering checks when links/rendering are affected; presentation-only copy,
  styling, markup, or layout → a diff or one visual check; styling/markup/attributes that change
  accessibility, security, or interaction behavior → focused behavior evidence.
- **Config or generated output:** its syntax, schema, or generation check.
- **Shared paths, contracts, sensitive areas:** broaden to all impacted packages/modules. **Full
  suite:** only for broad/high-risk fan-out or an explicit project rule — never a default local
  pre-PR run; configured CI is the merge gate, not a local duplicate.
- **UI/browser:** browser-based checks only when the change exercises a UI/browser flow; backend
  changes verify at the API level (Stage 5).

## Review topology (Stage 6 evidence binding)

Run reviews on a clean materialization of the complete target-to-tree delta; bind evidence to its
target, parent, and tree. After commit, require the tree to have the same reviewed content and its
parent to match. When a security record exists for the change, its reviewed-subject identities are
inputs to that check: verify the committed files still match them before the push, and rerun the
review on a mismatch. At final confirmation, resolve authoritative target/head tips by PR, remote-only,
or local-only mode and require a pending non-empty delta. Treat target CI policy as the baseline;
feature-side changes cannot reduce it, and approved additions or modifications must run from the
reviewed candidate revision. Accept head CI only when the target is its ancestor; otherwise
reproduce a synthetic `(target, head)` integration tree and review it against both parents. If head
or envelope topology differs from landing, accept its CI only for tree-only, topology-independent
checks; other checks must run on the actual landing candidate. Re-resolve tips, policy, and
workflow identity before the verdict. Stale refs, unreachable configured hosts, changed content, or
sensitive interactions block until applicable QA and reviews rerun. Classify feature and
integration deltas semantically against the canonical sensitive-area list and record the rationale.

## Security-review coverage

For every required planning or implementation security review, establish the intended file scope
before invoking a tool: relevant PRD, ADRs, contracts, architecture, threat model, implementation,
and tests — including staged, unstaged, and new/untracked artifacts. Record the base and reviewed
revision or content identity; do not stage or commit files merely to make them visible. A scope
resolver that reads only committed deltas under-counts an uncommitted working tree; its report is
then not authoritative for coverage — the manual review establishes it, and the record says so.
When several plans share one working tree, each review's scope is its own plan's delta: name
co-resident changes, including copies in other worktrees and stashes, and where each one's coverage
lives.

Compare the tool's actual file coverage with that scope. Filtered Markdown, tests, untracked files,
an empty result, or unknown coverage do not count as reviewed. Read omitted files directly and
perform the **structured manual review**: changed trust boundaries; authentication and
authorization; data exposure; abuse cases; dependencies; hostile inputs — reconciling the intended
file scope with actual coverage under sdlc, including docs, tests, and new files. Record each file
as tool-reviewed, manually reviewed, or excluded with a scope-specific reason, along with the
reviewed identity, limits, findings, and resolutions, in `docs/security.md`. Exclusions
cannot waive relevant sensitive changes. If required content is inaccessible, report incomplete
coverage and block the planning landing or implementation readiness rather than returning a clean
verdict — even when a tool reports no findings. No particular agent runtime is required.

Record coverage and verification limits in a dated record under `docs/security/records/` — the
actual write date, UTC, not an expected review or merge date — and add
its current entry to the index in `docs/security.md`. After substantive edits, refresh the affected
review and its coverage identity. A planning review certifies the design only, never runtime
enforcement.

## Amending decisions mid-implementation

An ADR or PRD states current intent; it is not authority for its own sake. When implementation
shows a recorded decision is wrong, amend the record rather than building around it — in the same
change as the code, never as silent divergence.

- Edit a Proposed or Accepted ADR in place only while it is unimplemented and dependency-free.
  After amending an Accepted ADR: renew human approval and re-freeze any affected contract before
  implementation resumes.
- For an implemented or depended-on ADR: add a superseding ADR, renew human approval before
  implementation resumes, re-freeze any affected contract, mark the old one
  `Superseded by ADR-NNNN`, and name the assumption that turned out false rather than the
  alternative looking simpler.
- Route by artifact class: an internal ADR follows this matrix; a shipped contract with a deployed
  consumer needs the versioning/deprecation decision (`AGENTS.md` → Guardrails); one without a
  deployed consumer may change outright under this matrix with applicable approval and re-freeze.
- Every PRD requirement or scope amendment returns to human approval. A reversal that invalidates
  the rest of the plan belongs at the plan gate, not absorbed into the diff. If you cannot say why
  the old decision was wrong, the objection is probably inconvenience.

## Lifecycle triggers at Land

Before Land, re-evaluate lifecycle triggers: compare the intended deployment or promotion and the
candidate Lifecycle/production-register rows with the target baseline recorded by
`definition-of-done-review` during local readiness. Evaluate target rows even if the candidate
deletes or weakens them. A candidate **downgrade** of a target Lifecycle row is a policy change
requiring a durable, human-approved decision (ADR or production register) with factual evidence the
relevant consumer, data, or traffic is absent; fulfilling a deferred row does not itself authorize
the downgrade. **Deletion or weakening** of a target row or trigger is an additional policy change
requiring a durable, human-approved retirement decision recording factual evidence that the
deferred work is fulfilled and verified or the trigger no longer applies. If the merge reaches a
trigger, the deferred work must be on the target or in the reviewed landing candidate and verified
before promotion; the pre-merge lifecycle state is not sufficient to defer it.

## DB schema changes

Expand/contract (migrate → deploy → clean up) **once the table holds real data or any deployed
process reads or writes it** — a deployed _writer_ breaks on a renamed/dropped column or a new
required one just as a reader does. Before that, change it outright.
