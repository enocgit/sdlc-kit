---
name: address-review
description: >
  Triages review comments on an open pull request — from humans and from bots (CodeRabbit, bugbot,
  Codex, Sourcery, …) — and addresses them. Reads every comment, verifies and challenges each one
  against the code, the frozen contract, and the ADRs to weed out false positives, then auto-fixes
  the trivial and gates the rest behind a plan. Manually invoked, standalone — not tied to a
  pipeline stage. Use when the user says "address the PR reviews", "go through CodeRabbit's
  comments", "handle the bugbot findings", "handle the codex findings" or "respond to the review".
---

# address-review

Work through the review comments on an open PR and resolve them **deliberately**. Reviewers — and
especially bots — are high-recall, low-precision: a large share of their comments are false
positives, style nits, or misreadings of the contract. Blindly "fixing everything a reviewer said"
is net-negative. The job of this skill is to **triage first, challenge each comment, then act** —
fixing what's real, refuting what isn't (with rationale), and deferring what's out of scope.

This is standalone and **manually invoked** — it isn't bound to a pipeline stage. But it inherits
the kit's conventions: the frozen contract is authoritative, sensitive areas (canonical list in
the project's `AGENTS.md` → Sensitive areas) get extra care, comments cite the durable doc
(ADR/PRD/contract) not the pipeline, and outward-facing actions and merges stay the human's call.

It is **not** a second `code-review`. `code-review` proactively audits your own diff before you
push; this skill reactively triages what *reviewers* already said on an open PR. If a comment
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

2. **Triage each comment — verify and challenge.** Do not take a comment at face value. Check each
   against the actual code, the frozen contract, and the relevant ADR/PRD. Assign a verdict and
   print a triage table **before touching anything**:

   | Comment (source · location) | Verdict | Planned action |
   |---|---|---|
   | … | **Valid** / **False positive** / **Out of scope** / **Nit** | … |

   - **Valid** — a real defect; the reviewer is right.
   - **False positive** — wrong, or already handled; the code is correct as written.
   - **Out of scope** — legitimate but not this PR's job.
   - **Nit** — style/preference, no correctness impact.

3. **Act by verdict — auto-fix trivial, gate the rest.**
   - **Nit / trivially-correct fix** (typo, rename, obviously-safe guard) → apply it and disclose
     it in the report. No gate.
   - **Valid + non-trivial** (touches logic, a sensitive area per `AGENTS.md`, or the contract)
     → **STOP and gate**: present a short per-fix plan and get approval before editing. A comment
     that implies changing a *shipped/frozen* contract is a decision — raise a new ADR, don't
     silently edit the interface.
   - **False positive** → do **not** change code. Draft a brief reply explaining why, citing the
     doc that settles it ("the frozen data contract 0001 permits null here", not "this is fine").
   - **Out of scope** → file a `task` issue (shaped per `.github/ISSUE_TEMPLATE/task.md`) and note
     the issue number in a reply; don't scope-creep the PR.

4. **Replies & thread resolution are outward-facing — confirm first.** Draft all replies as text
   and show them. Only post to GitHub (`gh pr comment` / `gh api ... /replies`) or resolve threads
   **after the user confirms**. Never resolve a thread you refuted without the reviewer/user seeing
   the rationale, and never merge.

5. **Report.** Summarize: what was **fixed** (with the commit-ready diff), what was **refuted** and
   why, what was **deferred** (issue #s), and what still **needs the user's decision** at a gate.
   End with a QA checklist if any fix warrants manual verification.

## Rules

- **Triage before acting.** Always show the verdict table first; never start editing off a raw
  comment list.
- **Challenge, don't comply.** A reviewer — human or bot — can be wrong. Refuting a comment with a
  clear, doc-backed rationale is a first-class outcome, not a failure to "address" it.
- **Auto-fix only the trivial + obviously-correct.** Anything touching logic, a sensitive area, or
  the contract is gated behind a plan approval (auto-fix trivial, gate the rest).
- **The contract is frozen.** A comment that wants a shipped-contract change is a new ADR, not an
  inline edit.
- **Outward-facing = confirm.** Posting replies and resolving threads need explicit go-ahead;
  merging is always the human's call. Don't commit or push unless asked.
- **Cite docs, not stages** in any code comments or replies you write.
