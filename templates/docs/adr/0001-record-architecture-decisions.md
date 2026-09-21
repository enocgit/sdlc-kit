# ADR 0001 — Record architecture decisions

- **Status:** Accepted
- **Date:** YYYY-MM-DD

## Context

We want a durable, append-only history of significant technical decisions so that future
engineers and AI agents understand _why_ the system is the way it is — without reverse-
engineering it from code. Architecture decisions are easy to forget and expensive to relearn.

## Decision

We will record each significant decision as a numbered ADR in `docs/adr/`, using the template in
`adr/TEMPLATE.md`. ADRs are append-only: we don't rewrite history. When a decision changes, we
add a new ADR and mark the old one **Superseded by ADR-NNNN**.

Superseding is normal, not a failure. When implementation shows an ADR was wrong, replace it in the
same change as the code and record which assumption turned out false. Keep building to the recorded
decision only while it still holds.

A decision is "significant" if it affects structure, a public API/contract, a cross-cutting
concern, or would surprise a competent newcomer.

## Consequences

- The current system _shape_ lives in `docs/architecture.md`; the _why/history_ lives here.
- Approving an ADR is a project decision. A shipped-contract change requires a new ADR.
- The log holds decisions, not a current instruction manual: read the newest ADR on a topic.
- Small reversible choices don't need an ADR — keep the log signal-rich.

## Alternatives considered

- **No ADRs / tribal knowledge** — rejected: doesn't survive team changes or agent handoffs.
- **Decisions only in PR descriptions** — rejected: not discoverable later.
