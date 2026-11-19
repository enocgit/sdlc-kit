---
name: address-review
description: >
  Triages review comments on an open pull request, from humans and bots (CodeRabbit, bugbot, Codex,
  Sourcery), verifies each against the code and the project's docs, fixes what is real, and refutes
  what is not. Manually invoked. Use when the user says "address the PR reviews", "go through
  CodeRabbit's comments", "handle the bugbot findings", or "respond to the review".
---

# address-review

Reviewers, bots especially, report many false positives. Fixing everything a comment asks for makes
the code worse; verify each one first.

Invoking this skill approves fixes, commits, pushes to the PR branch, and brief replies. A changed
decision, a sensitive or contract change, a new issue, and a merge still ask the developer.

## Steps

1. **Find the PR** from the current branch (`gh pr view`); ask only when there is none or several.
   Read every comment: `gh pr view --comments`, `gh api repos/{owner}/{repo}/pulls/{n}/comments`,
   and `.../reviews`. If `gh` is not authenticated, say so and stop.
2. **Keep the actionable ones:** a requested change, a reported defect, a question, a concern. Drop
   praise, boilerplate, outdated comments, and anything already answered; dropped comments get no
   reply.
3. **Triage before editing.** Check each against the code, the spec, the ADRs, and any frozen
   contract, and show a table of comment, verdict, and planned action:
   - **Valid:** fix it with a test where behavior changes, and commit. Follow-up commits only; a
     force-push while review is open destroys the reviewer's anchors.
   - **Decision:** it contradicts a spec, ADR, or contract, or asks for a redesign. Draft the reply
     and stop for the developer.
   - **False positive:** no code change; reply with the reason and the doc or code that settles it.
   - **Out of scope:** propose an issue and ask before creating it.
   - **Nit:** fix it if trivial, otherwise say no briefly.
4. **Push and reply** ("fixed in `<sha>`", refutations, issue proposals). Replies are short and
   cite the product's docs, not this workflow. Never resolve others' threads or merge.
5. **Report** only the sections with entries: Fixed (comment → commit and test), Refuted, Proposed
   issues, Needs your decision.
