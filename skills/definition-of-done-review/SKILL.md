---
name: definition-of-done-review
description: >
  Reviews a change against this team's Definition of Done before merge. It goes beyond generic code
  review by checking acceptance criteria, contract fidelity, proportional verification with test
  coverage where behavior warrants it, docs/ADR updates, and security for sensitive areas, then
  gives a pass/fail verdict with evidence appropriate to each item. Use at Stage 6 after code-review
  and code-simplification, or when the user asks "is this ready to merge" or "run the DoD check".
---

# definition-of-done-review

Run this team-specific check after generic `code-review` and `code-simplification`. Those checks catch bugs and
cleanup issues; this one verifies readiness against the team's standard.

## Review modes

### Local readiness before Land

Check every locally verifiable DoD item before push or PR creation. Resolve `reviewTarget` as the
exact tip of the human-designated landing branch: fetch its configured authoritative remote when one
exists, or use the human-designated local tip whenever no authoritative remote exists, regardless of
tracker mode. An unreachable configured remote blocks local readiness. Build a versioned SHA-256
identity for the prospective Git tree or the already-committed tree. Choose one evidence path:

- **Prospective review:** record `reviewBase` as the exact pre-commit `HEAD`. Build the prospective
  tree through a temporary index: from the repository root, create a mode-`0700` temporary directory
  and use a nonexistent path inside it as `GIT_INDEX_FILE`; clean the directory with a trap.
  Initialize that index with `git read-tree "$reviewBase^{tree}"`, then run `git add -A` against it;
  never modify the real index. This makes Git apply the active attributes and clean filters exactly
  as it will during the commit. A missing or failed filter blocks readiness rather than falling back
  to raw working-tree bytes.
- **Already-committed review:** require
  `git status --porcelain=v1 --untracked-files=all` to be empty. Set `reviewedCommit` to the exact
  `HEAD` and `reviewBase` to its sole direct parent. Review the existing commit tree. Do not create
  an empty commit merely to attach evidence.

Use Git's canonical tree object instead of reimplementing path and object serialization. Let
`format` be the ASCII output of `git rev-parse --show-object-format`. Let `tree` be the ASCII object
ID from `GIT_INDEX_FILE={temporary-index} git write-tree` for prospective review or from
`git rev-parse "$reviewedCommit^{tree}"` for Already-committed review. For each command, remove
exactly its single terminal LF; reject a missing or additional LF or any other ASCII whitespace.
Require `format` to be exactly `sha1` or `sha256` and `tree` to be lowercase hexadecimal of 40 or 64
characters, respectively. Start SHA-256 with the bytes `sdlc-reviewed-tree-v2\0`; append `format`
and `tree` in that order, each framed as its unsigned 64-bit big-endian byte length followed by its
bytes, and emit the digest as 64 lowercase hexadecimal characters. `git write-tree` recursively
covers directory trees, regular and executable blobs, symlinks, gitlinks, tracked changes,
non-ignored untracked files staged by `git add -A`, and deletions. Record `format`, `tree`, and the
resulting digest.

Use a clean materialization of the recorded tree, not the mutable source worktree, for local QA,
`code-review`, `code-simplification`, and `security-review`. For prospective review, create an unreferenced
evidence commit with `git commit-tree`. Give it the recorded `tree`, `reviewBase` as its sole parent,
and fixed identity, timestamps, and message; never update a ref. For Already-committed review, use
`reviewedCommit` as the evidence commit. Create a mode-`0700` temporary parent for a detached private
worktree at a nonexistent child path with `git worktree add --detach`. Install a trap that runs
`git worktree remove --force` before removing the private parent.

Create and destroy a fresh detached private worktree for every cited check. Materialize every submodule
at its recorded gitlink. Before and after each check, rebuild the tree identity from that worktree and
verify recursive submodule state. A mismatch discards the evidence and requires a fresh worktree and
rerun. This prevents ignored, untracked, generated, and submodule residue from one check affecting the
next. Reviews must cover the complete `reviewTarget`-to-tree delta, not only `reviewBase..HEAD`.

For `security-review`, the recorded subject identity excludes or normalizes only the review-record metadata in `docs/security.md` as specified by that skill. Record-only updates to those fields do not invalidate the security subject review; substantive changes to its threat model, baseline controls, or reviewed scope require rematerialization and a fresh security review.

After prospective review, require the new commit's sole direct parent to equal `reviewBase`, set
`reviewedCommit` to that commit, obtain its tree, and require all three recorded identity values to
match. For Already-committed review, record those values directly from `reviewedCommit`. A different
parent or tree invalidates the evidence. Re-run every commit-metadata or topology-dependent local
check against the actual `reviewedCommit`; prospective evidence may be reused only for demonstrably
tree-only checks. Record the authoritative required-check policy and workflow baseline during local
readiness, including each workflow's immutable revision or content digest, expected event, producer,
and required check names. In prospective mode, report _tree reviewed; commit verification pending_
until the authorized commit exists, its parent and tree match, and every metadata- or
topology-dependent check passes against `reviewedCommit`. Do not push or open a PR before that pass.
Only then may local readiness report _locally ready; final confirmation blocked on CI_ when required
CI needs a push or PR. Any other failed item blocks Land. Record the target-side Lifecycle values and
production-register rows, triggers, and owners as the target register baseline, then apply the
conductor's `Before Land, re-evaluate lifecycle triggers` rule, which is the canonical statement of
the downgrade, retirement, and trigger requirements.

### Final confirmation before merge

After required CI finishes, or immediately when no CI workflow exists, re-read the canonical DoD.
Resolve authoritative integration refs by mode: for a PR, fetch the host's PR base and head; without
a PR but with a remote, fetch the human-designated target and pushed feature branches; without a
remote, resolve the human-designated local target and feature tips. Record `targetBase` and
`authoritativeHead`; stale refs, an unreachable configured host, or ambiguous branches block.
Require `authoritativeHead` to equal `reviewedCommit` and every applicable head-CI SHA. Bind each
result to its expected provider, workflow or pipeline identity, expected event, immutable definition
revision or content digest, and accepted OID. If the provider cannot expose these bindings, fail
closed unless the human records explicit approval for that limitation. Reject merge readiness if
the tips are equal, if `authoritativeHead` is already reachable from `targetBase`, or if their trees
are identical. Treat those cases as post-land or empty-change audits, never as pending Land work.

Determine required checks from the authoritative target's CI policy, branch protection, and
configured external CI before evaluating feature changes. Re-resolve the policy and workflow baseline
recorded during local readiness. Treat that policy and its workflow set as
a non-reducible baseline. A feature-side deletion, rename, or weakening cannot make a baseline check
N/A without an explicit human-approved policy change. Review CI-configuration changes and add every
approved new or modified check to the expected set. Require every configured or policy-required check from its trusted producer and expected event;
common checks include lint, typecheck, test, build, contract, dependency-advisory, and E2E.
Baseline checks must satisfy the recorded baseline identity and definition digest; new or modified
checks must run from the recorded candidate-side CI revision and bind to its identity and digest. CI
is N/A only when
the target defines no CI workflow or required check, no external CI is configured, and the candidate
adds none.

If reviewed content changed after local readiness, `targetBase` differs from `reviewTarget`, or the
candidate tree differs from the locally reviewed tree, rerun applicable QA, `code-review`,
`code-simplification`, `security-review`, and the full local-readiness review against a clean materialization
of the complete target-to-candidate delta. A changed parent invalidates the same evidence even when
the tree is identical.

Accept head CI only when `targetBase` is an ancestor of `authoritativeHead`. Otherwise require one
verified synthetic merge commit whose first direct parent is exactly `targetBase` and whose second
is exactly `authoritativeHead`. Reproduce its tree with the documented integration-tree construction
that landing will use: merge, squash application, or rebase replay with the same options, merge
drivers, and conflict resolutions. Require an exact tree match and review the synthetic delta
against both parents. Record a semantic comparison against the canonical sensitive-area list for
both the feature and integration deltas; path-only classification is insufficient. Rerun targeted
`security-review` when either delta touches a sensitive area. If it is N/A, record why.

Prefer CI on the actual landing topology. Head CI on a non-final topology and CI on a two-parent
evidence envelope are acceptable only when every required check is demonstrably tree-only and
topology-independent. This restriction applies when squash, rebase, or a merge commit will replace
the tested head topology. A topology-dependent check, including one that reads parents, commit
metadata, `git diff HEAD^`, or `git describe`, must run on the actual landing candidate OID.
Hosting-provider merge SHAs need the same guarantees.

Immediately before the verdict, resolve both authoritative tips, the required-check policy, and the
workflow baseline again. Re-apply the conductor's `Before Land, re-evaluate lifecycle triggers` rule
against the target register baseline recorded during local readiness. Reject the evidence if any
changed, including a workflow identity, immutable revision, or content digest whose required check
names stayed the same. Confirmation also fails if integration-tree construction is unknown, candidate
trees differ, or the required-check baseline weakened without explicit human approval, or any required
CI result is not bound to the accepted head, synthetic, or actual landing OID. When CI is N/A, all
ancestry, tree, and integration-review checks still apply. Then confirm every pending item and give the
full pass/fail verdict. Do not report the change as ready to merge until this confirmation passes.

## Checklist — read it from AGENTS.md, don't rely on a copy

The **canonical Definition of Done lives in the project's `AGENTS.md`** ("Definition of Done"
section). Read it at run time and review the change against **that exact list**, item by item. This
skill deliberately embeds no copy, so a project that tightens or extends its DoD is automatically
reviewed against its own standard. The sensitive-areas list is likewise canonical in `AGENTS.md` →
Sensitive areas.

How to judge the items that need interpretation:

- **Acceptance criteria.** Quote each criterion from the PRD/issue and map it to evidence.
- **Contract fidelity.** When an integration contract applies, require no undocumented
  endpoints/fields and derive types from the contract rather than duplicating them. A shipped contract
  with a deployed consumer requires the versioning/deprecation ADR and compatibility decision before
  an interface change; only when there is no deployed consumer may the ADR matrix route apply, with
  applicable approval, a re-freeze, and a production-register deferral. For fast-path work with no
  integration contract, accept N/A only with a concrete rationale.
- **Verification / observed working.** Evidence must match the risk: apply the verification
  standard in `AGENTS.md` (proportional local checks, no full suite merely because CI defines
  lint/typecheck/test/build, browser evidence only when the change can break the flow it
  exercises — a run that could not have failed proves nothing). Runtime-affecting work must be
  exercised and observed with the available runtime tools. Do not fail a change merely because its
  best proof is not a new test, and do not accept an assertion that only restates a presentation
  rule as proof. Configured CI checks remain required from their trusted producer before merge.
  While the Lifecycle block in `docs/context.md` shows no deployed consumer, real data, or traffic,
  defer only failures whose required deployed consumer, real data, deployment, load, traffic, or
  multi-version condition is unavailable; record the deferral in the production register.
- **Docs.** Update `docs/architecture.md` if the system's shape changed. Edit a Proposed or Accepted
  ADR in place only while it is unimplemented and dependency-free; after amending an accepted ADR,
  require renewed human approval and re-freeze any affected contract before implementation resumes.
  Require a superseding ADR in the same change when an implemented or depended-on ADR was disproved,
  regardless of status, then require human approval before implementation resumes and re-freeze any
  affected contract. For contract changes, apply the exclusive deployed-consumer routing in Contract
  fidelity before this generic ADR rule. Every PRD requirement or scope amendment returns to human approval.
  When the change has a tracker issue, ensure it reflects reality. Decision states (approval,
  acceptance, freeze) are stated by their artifacts; live delivery state is stated only by the
  tracker — no doc may carry intermediate status prose.
  Current-behavior claims and security controls must reflect the task's evidence,
  with planned and partial behavior identified. Full epic reconciliation may wait for the final
  child; inaccurate claims about enforced behavior may not. Link evidence, not duplicate task lists.
- **Stale-claim scan (mechanical).** In the changed docs, search for intermediate status tokens
  (`PENDING`, `TODO`, `In progress`, `Partially implemented`, `Planned`), template markers, and
  statements of delivery state outside the tracker and ADRs. For each hit: if it is live state, it
  moves to the tracker or is deleted; if it is a decision record, it moves to the ADR; if it is a
  current-behavior claim, require evidence from this change or a dated link to its source. Record
  the scan (patterns, files, hits, resolutions) as local-readiness evidence — a claimed-clean scan
  without the recorded patterns and hits is not evidence.
- **Readability.** Review changed docs, issue criteria, and proposed PR text against `AGENTS.md`'s
  one-point writing rule; identify overloaded points rather than enforcing word or sentence quotas.
  Split independent obligations while preserving exact conditions, requirement IDs, document
  structure, and introductory paragraphs.
- **Code comments.** Check comments in changed code against `AGENTS.md`'s comment standard.
  Verify claims about authorization, ownership, persistence, retries, and failure guarantees against
  the implementation and relevant evidence; comments are not proof of correctness.
  Flag missing explanations where non-obvious constraints could cause an incorrect future change.
  Remove stale or syntax-narrating comments rather than requiring comments on every function.
- **Security.** Require a recorded semantic sensitive-area assessment even when `security-review` is
  N/A. For sensitive-area changes, require a completed review, resolved findings, and an updated
  `docs/security.md`. Apply the conductor's Security-review coverage protocol: reconcile the intended
  scope with actual tool/manual coverage at the reviewed revision or content identity, including
  new files and relevant docs/tests. Require reasons for exclusions, manual review for tool omissions,
  and refreshed review after substantive edits. Empty or unknown tool coverage is not a pass;
  inaccessible required files block readiness. Planning evidence does not certify runtime controls.

## Output

Produce a verdict per item with evidence appropriate to that item: file:line, command output, CI
check URL/result, runtime observation, or tracker URL/status. Use N/A only with a concrete
rationale.
In local-readiness mode, distinguish pass, fail, and CI-pending. In final-confirmation mode, produce
only the full pass/fail verdict. If anything fails, list the exact follow-ups and do not mark the
task ready to merge.
