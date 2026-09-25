# PRD NNNN: {title}

> Follow the documentation writing standard in AGENTS.md. Keep this scan-first: approval, scope,
> decisions, constraints, links, and open questions before detail. Delete unused sections in the
> filled PRD. State nothing about implementation progress — the tracker owns live state; this
> document's delivery record is written once, when the feature is true.
>
> **Amending an approved PRD:** write a new amendment PRD that states the changed requirements and
> supersedes the superseded ones; link both directions. Do not rewrite approved requirements in
> place.

## Summary

- **Approval:** Draft | Approved
- **Delivery:** {write once, at final reconciliation only: what shipped, with evidence links —
  delete this line until then; the tracker owns intermediate state}
- **Outcome:** {one sentence describing the intended result}
- **Scope:** In — {short list}; Out — {short list}
- **Key decisions:** {decision summary or links}
- **Constraints:** {hard product, technical, legal, or operational limits}
- **Links:** {brief, epic, designs, ADRs, contracts}
- **Open questions:** {questions to resolve before approval, or None}
- **Owner / date:** {name} / YYYY-MM-DD

## Problem

<!-- What's broken/missing and for whom. Link the brief if there is one. -->

## Users & goals

- **{persona}** wants to {goal} so that {outcome}.

## Success metrics

<!-- Measurable. How we'll know this worked. -->

- {metric and target}

## Requirements

### Functional

- FR1: {requirement}

### Non-functional

- NFR1: {perf / security / availability / accessibility}

## UX notes

<!-- Key screens/flows. Link designs. -->

## Data & contract impact

<!-- New/changed entities, endpoints, events. The precise interface lives in docs/contracts/
     and the codebase; name what changes here. -->

## Acceptance criteria

<!-- Testable. Each criterion should map to a verification step. -->

- [ ] {criterion}

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| {risk} | L/M/H | L/M/H | {plan} |
