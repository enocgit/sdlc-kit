---
name: Epic (feature)
about: A user-facing feature (its PRD) tracked as an epic with sequenced child tasks
title: "[epic] "
labels: ["epic"]
---

<!-- The PRD in docs/prd/ is the source of truth. Link child tasks as sub-issues in build
     order; the sub-issues list is the epic's record of task state.
     Fill the reference line, then delete refs that don't apply. -->

**PRD:** `docs/prd/NNNN-*.md` · **ADR:** NNNN · **Contract:** NNNN · **Threat model:** `docs/security.md` (if sensitive)

## Goal

<!-- One short paragraph: the problem and who benefits. Link the parent feature if there is one. -->

## Model (ADR-NNNN)

<!-- Optional — only when the feature introduces a data model. 2–3 lines on the key entities /
     the decision. Delete this section if there's nothing to model. -->

## Definition of Done (epic)

- [ ] All child task DoDs met
- [ ] PRD acceptance criteria pass end-to-end
- [ ] `security-review` closed for any sensitive tasks
- [ ] Contract NNNN implemented as frozen (no silent changes)
