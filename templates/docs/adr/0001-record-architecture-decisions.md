# ADR 0001 — Record architecture decisions

- **Status:** Accepted
- **Date:** YYYY-MM-DD

## Context

We want a durable, append-only history of significant technical decisions so that future
engineers and AI agents understand *why* the system is the way it is — without reverse-
engineering it from code. Architecture decisions are easy to forget and expensive to relearn.

## Decision

We will record each significant decision as a numbered ADR in `docs/adr/`, using the template in
`adr/TEMPLATE.md`. ADRs are append-only: we don't rewrite history. When a decision changes, we
add a new ADR and mark the old one **Superseded by ADR-NNNN**.

A decision is "significant" if it affects structure, a public API/contract, a cross-cutting
concern, or would surprise a competent newcomer.

## Consequences

- The current system *shape* lives in `docs/architecture.md`; the *why/history* lives here.
- Approving an ADR is a pipeline gate (Stage 2). A shipped-contract change requires a new ADR.
- Small reversible choices don't need an ADR — keep the log signal-rich.

## Alternatives considered

- **No ADRs / tribal knowledge** — rejected: doesn't survive team changes or agent handoffs.
- **Decisions only in PR descriptions** — rejected: not discoverable later.
