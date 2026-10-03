---
name: address-review
description: >
  Triages review comments on an open pull request — from humans and from bots (CodeRabbit, bugbot,
  Codex, Sourcery, …) — and addresses them. Reads every comment but acts only on the actionable
  ones, verifying and challenging each against the code, the frozen contract, and the ADRs to weed
  out false positives, then fixes what is real and refutes what isn't. Manually
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
the project's `AGENTS.md` → Sensitive areas) get extra care, and comments cite the durable doc
(ADR/PRD/contract) rather than the pipeline. Invoking this skill **is** the approval: fixing,
committing, pushing the PR branch, and posting brief replies proceed without further asks. Only a
decision reversal, a sensitive-area or contract change, an external issue creation, or a merge
still gates — merge ownership follows `sdlc`'s landing rules.

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
   - **Decision** — actionable only by changing a decision: the comment contradicts the frozen
     contract, an ADR, or the PRD, or asks for a redesign. These are Stage 2-class questions
     wearing a comment's clothing.
   - **False positive** — wrong, or already handled; the code is correct as written.
   - **Out of scope** — legitimate but not this PR's job.
   - **Nit** — style/preference, no correctness impact.

4. **Act by verdict.**
   - **Valid** (trivial or not) → fix it, verify proportionally to the risk, and commit. Follow-up
     commits only — never force-push while review is open: it destroys the reviewer's inline
     comment anchors and the reviewed diff.
   - **Decision** → **STOP and gate.** Draft the reply, but the human decides the question; apply
     the conductor's amending rules for the ADR, contract, and PRD routes before any code change,
     and record any deferral in the `docs/context.md` production register. A reply that reopens a
     decision is a decision ask, not a comment reply.
   - **False positive** → do **not** change code. Post a brief reply explaining why, citing the
     doc that settles it ("the frozen data contract 0001 permits null here", not "this is fine").
     Keep it short — the reply posts unseen, so brevity is the safeguard, and it cites the artifact,
     not the pipeline.
   - **Out of scope** → propose a `task` issue (shaped per `.github/ISSUE_TEMPLATE/task.md`) and
     **ask before creating it** — an external issue is an outward write. Do not scope-creep the PR.

5. **Push and post — no bundle ask.** After fixes are validated and committed: push the branch and
   post the replies ("fixed in `<sha>`", refutations, issue pointers) directly. Keep replies brief
   and cite the durable doc. Do not resolve other people's thread states beyond replying, and never
   merge.

6. **Report the ledger.** Summarize: what was **fixed** (commit refs), what was **refuted** and
   why, what was **deferred** or **proposed** (issues suggested but not created), and what still
   **needs the user's decision** at a gate.
   End with a QA checklist if any fix warrants manual verification.

## Rules

- **Only actionable comments.** Praise, agreement, and boilerplate are read but never triaged,
  replied to, or resolved.
- **Triage before acting.** Always show the verdict table first; never start editing off a raw
  comment list.
- **Challenge, don't comply.** A reviewer — human or bot — can be wrong. Refuting a comment with a
  clear, doc-backed rationale is a first-class outcome, not a failure to "address" it.
- **Invoking the skill is the approval** for fixes, commits, pushes, and replies. Decision
  reversals, sensitive-area or contract changes, external issue creation, and merges still gate.
- **The contract is frozen.** Contract changes follow the conductor's `Amending a decision
  mid-implementation` rules; a change to a shipped contract with a deployed consumer needs a
  versioning/deprecation ADR, not an inline edit.
- **No force-push while review is open.** Follow-up commits only; a force-push destroys the
  reviewer's inline-comment anchors and the reviewed diff.
- **Brief replies, citing docs, not stages.** Replies post unseen, so they stay short and cite the
  durable doc (ADR/PRD/contract), never the pipeline.
