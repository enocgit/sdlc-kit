# ADR 0001 — Record architecture decisions

- **Status:** Accepted
- **Date:** YYYY-MM-DD

## Context

We want a durable history of significant technical decisions so that future
engineers and AI agents understand _why_ the system is the way it is — without reverse-
engineering it from code. Architecture decisions are easy to forget and expensive to relearn.

## Decision

We will record each significant decision as a numbered ADR in `docs/adr/`, using the template in
`adr/TEMPLATE.md`. Edit a Proposed or Accepted ADR in place only while it is unimplemented and
dependency-free. After amending an accepted ADR, renew human approval and re-freeze any affected
contract before implementation resumes. When an implemented or depended-on decision changes, add a
new ADR, renew human approval before implementation resumes, re-freeze any affected contract, and
mark the old one **Superseded by ADR-NNNN** in the same change as the code, regardless of its status.

Superseding is normal, not a failure. When implementation shows an implemented decision was wrong,
record which assumption turned out false. A decision nobody implemented and nothing depends on is
edited in place instead: this log records decisions the project built on, not proposals it walked
away from.

A decision is "significant" if it affects structure, a public API/contract, a cross-cutting
concern, or would surprise a competent newcomer.

## Consequences

- The current system _shape_ lives in `docs/architecture.md`; the _why/history_ lives here.
- Approving an ADR is a project decision. A shipped contract with a deployed consumer requires a
  versioning/deprecation ADR; if there is no deployed consumer, apply the amendment matrix and
  re-freeze the contract.
- The log holds decisions, not a current instruction manual: read the newest ADR on a topic.
- Small reversible choices don't need an ADR — keep the log signal-rich.

## Alternatives considered

- **No ADRs / tribal knowledge** — rejected: doesn't survive team changes or agent handoffs.
- **Decisions only in PR descriptions** — rejected: not discoverable later.
