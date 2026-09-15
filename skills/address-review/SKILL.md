---
name: address-review
description: >
  Triages review comments on an open pull request — from humans and from bots (CodeRabbit, bugbot,
  Codex, Sourcery, …) — and addresses them. Reads every comment but acts only on the actionable
  ones, verifying and challenging each against the code, the frozen contract, and the ADRs to weed
  out false positives, then auto-fixes the trivial and gates the rest behind a plan. Manually
  invoked, standalone — not tied to a pipeline stage. Use when the user says "address the PR
  reviews", "go through CodeRabbit's comments", "handle the bugbot findings", "handle the codex
  findings" or "respond to the review".
---

# address-review

Work through the review comments on an open PR and resolve them with evidence. Reviewers — and
especially bots — are high-recall, low-precision: a large share of their comments are false
positives, style nits, or misreadings of the contract. Blindly "fixing everything a reviewer said"
is net-negative. So is answering comments that asked for nothing. The job of this skill is to
**select what's actionable, challenge it, then act** — fixing what's real, refuting what isn't
(with rationale), and deferring what's out of scope.

This is standalone and **manually invoked** — it isn't bound to a pipeline stage. But it inherits
the kit's conventions: the frozen contract is authoritative, sensitive areas (canonical list in
the project's `AGENTS.md` → Sensitive areas) get extra care, comments cite the durable doc
(ADR/PRD/contract) not the pipeline, and outward-facing actions and merges stay the human's call.

It is **not** a second `code-review`. `code-review` proactively audits your own diff before you
push; this skill reactively triages what _reviewers_ already said on an open PR. If a comment
prompts a broader re-audit, that's `code-review`'s job — route back to it.

## Steps

1. **Identify the PR — infer, don't interrogate.** Resolve it from the current branch
   (`gh pr view` with no number returns the open PR for the checked-out branch), so right after
   you've landed a task the skill already knows which PR this is — state it and move on. Only ask
   the user when there's no PR for the branch or several plausible candidates. Then pull the full
   comment set via `gh` — conversation comments, inline review comments, and bot review summaries:
   - `gh pr view [n] --comments` (top-level + review summaries)
   - `gh api repos/{owner}/{repo}/pulls/{n}/comments` (line-anchored review comments)
   - `gh api repos/{owner}/{repo}/pulls/{n}/reviews` (review verdicts, incl. bot reviews)

   If `gh` isn't authenticated, say so and stop.

2. **Select the actionable set.** Read every comment, then carry forward only the ones that ask
   for something: a requested change, a reported defect, a question that needs an answer, or a
   raised concern. Drop the rest — praise, agreement, "LGTM", bot summary boilerplate, thread
   chatter, outdated comments on lines the diff already changed, and anything the PR author already
   answered. Dropped comments are not triaged, not replied to, and not resolved. Where one thread
   mixes both, carry forward only the actionable part.

3. **Triage each actionable comment — verify and challenge.** Do not take a comment at face value.
   Check each against the actual code, the frozen contract, and the relevant ADR/PRD. Assign a
   verdict and print a triage table **before touching anything**:

   | Comment (source · location) | Verdict | Planned action |
   |---|---|---|
   | … | **Valid** / **False positive** / **Out of scope** / **Nit** | … |

   - **Valid** — a real defect; the reviewer is right.
   - **False positive** — wrong, or already handled; the code is correct as written.
   - **Out of scope** — legitimate but not this PR's job.
   - **Nit** — style/preference, no correctness impact.

4. **Act by verdict — auto-fix trivial, gate the rest.**
   - **Nit / trivially-correct fix** (typo, rename, obviously-safe guard) → apply it and disclose
     it in the report. No gate.
   - **Valid + non-trivial** (touches logic, a sensitive area per `AGENTS.md`, or the contract)
     → **STOP and gate**: present a short per-fix plan and get approval before editing. A comment
     that implies changing a _shipped/frozen_ contract is a decision — raise a new ADR, don't
     silently edit the interface.
   - **False positive** → do **not** change code. Draft a brief reply explaining why, citing the
     doc that settles it ("the frozen data contract 0001 permits null here", not "this is fine").
   - **Out of scope** → prepare a `task` issue (shaped per `.github/ISSUE_TEMPLATE/task.md`) and
     include its exact proposed title/body in the outward-action bundle. Use an explicit
     `{issue-number-or-url}` placeholder for any dependent reply or action; after approval, fill it
     from the create response within that same bundle. Do not scope-creep the PR.

5. **Prepare one outward-action bundle — confirm once.** After local fixes are validated, show
   the proposed commit and exact message, any external issue creation with its exact title/body,
   an explicit `{issue-number-or-url}` placeholder for dependent actions, the commit-ready diff and
   push target, and each thread-resolution action with its exact target. Ask for one approval
   covering that whole bundle. Do not create the commit or issue, push fixes, post replies, or
   resolve threads before approval. After approval, create the approved issue first, then fill its
   placeholder from the create response before performing dependent actions. Approval authorizes
   only the listed actions. Never include merge in the bundle.

   **Replies ride the bundle without preview.** Routine replies — "fixed in `<sha>`", a nit applied,
   a pointer to the issue just created — go out on approval; state how many, not what each says.
   Show the exact text only for a **critical** reply, and get approval for it with the rest of the
   bundle: a refutation telling a reviewer they are wrong, any claim about a shipped/frozen contract
   or a sensitive area, and any reply that declines or defers requested work.

6. **Report.** Summarize: what was **fixed** (with the commit-ready diff), what was **refuted** and
   why, what was **deferred** (including proposed issues that were not created), how many replies
   were posted, and what still **needs the user's decision** at a gate. Distinguish created issue
   numbers from unapproved proposals.
   End with a QA checklist if any fix warrants manual verification.

## Rules

- **Only actionable comments.** Praise, agreement, and boilerplate are read but never triaged,
  replied to, or resolved.
- **Triage before acting.** Always show the verdict table first; never start editing off a raw
  comment list.
- **Challenge, don't comply.** A reviewer — human or bot — can be wrong. Refuting a comment with a
  clear, doc-backed rationale is a first-class outcome, not a failure to "address" it.
- **Auto-fix only the trivial + obviously-correct.** Anything touching logic, a sensitive area, or
  the contract is gated behind a plan approval (auto-fix trivial, gate the rest).
- **The contract is frozen.** A comment that wants a shipped-contract change is a new ADR, not an
  inline edit.
- **Outward-facing = one confirmation.** The proposed commit and message, external issue creation,
  pushing validated fixes, posting replies, and resolving listed threads share one explicit approval
  when applicable. Routine replies go out on that approval unseen; critical replies — refutations,
  contract or sensitive-area claims, declined work — are shown in full first. Do not perform any
  listed action outside that approved bundle. Merging is always the human's call and is never part
  of the bundle.
- **Cite docs, not stages** in any code comments or replies you write.
