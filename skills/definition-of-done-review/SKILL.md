---
name: definition-of-done-review
description: >
  Reviews a change against this team's Definition of Done before merge — beyond generic code
  review — checking acceptance criteria, contract fidelity, test coverage at the right layer,
  docs/ADR updates, and security for sensitive areas, then gives a pass/fail verdict with
  file:line evidence. Use at Stage 6 after code-review and simplify, or when the user asks "is
  this ready to merge" or "run the DoD check".
---

# definition-of-done-review

A consistent, team-specific final check. Generic `code-review` and `simplify` catch bugs and
cleanup; this verifies the change is actually *done* by our standard. Run it after them.

## Checklist — read it from AGENTS.md, don't rely on a copy

The **canonical Definition of Done lives in the project's `AGENTS.md`** ("Definition of Done"
section). Read it at run time and review the change against **that exact list**, item by item —
this skill deliberately embeds no copy, so a project that tightens or extends its DoD is
automatically reviewed against its own standard. (The sensitive-areas list is likewise canonical
in `AGENTS.md` → Sensitive areas.)

How to judge the items that need interpretation:

- **Acceptance criteria** — quote each criterion from the PRD/issue and map it to evidence.
- **Contract fidelity** — no undocumented endpoints/fields; types derived from the contract, not
  hand-duplicated; any mismatch is a finding even if tests pass.
- **Tests / observed working** — green suite is necessary, not sufficient: the change must have
  been run and observed (`run`/`verify`), and new logic covered, not just touched.
- **Docs** — `docs/architecture.md` if the system's shape changed; a new ADR if a decision was
  made; the tracker issue reflects reality.
- **Security** — for sensitive-area changes, `security-review` was run with findings resolved and
  `docs/security.md` updated.

## Output

Produce a pass/fail verdict per item with file:line evidence. If anything fails, list the exact
follow-ups and do NOT mark the task ready to merge. This is a gate.
