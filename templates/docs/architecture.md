# Architecture

> Follow the documentation writing standard in AGENTS.md. This is the current system shape:
> use compact summaries, diagrams or small tables when useful, and links to ADRs/contracts for
> detail. Delete unused sections once filled. Decision _history_ lives in `docs/adr/`; update this
> document when the shape changes and link the ADR that caused it.

## System context

<!-- Who/what the system talks to. A C4 "context" view in prose or a diagram. -->

## Containers / services

<!-- The deployable pieces and how they communicate. -->

| Container | Responsibility | Tech | Talks to |
| --------- | -------------- | ---- | -------- |
| Web | UI | React + TS | API |
| API | Business logic | Node + TS | DB, external services |
| DB | Persistence | Postgres | — |

## Key components

<!-- Notable modules within containers and their boundaries. -->

## Data model

<!-- Core entities and relationships. Link to schema/migrations (the contract). -->

## Key flows

<!-- 1–3 important sequences (e.g. payment, signup). Prose or sequence diagram. -->

## Planned changes

<!-- Approved future changes only. Link the decision and contract; keep current behavior in the
     sections above. Separate decision status from delivery: Not implemented, Partially implemented,
     or Implemented. Link partial-delivery evidence rather than copying tracker checklists. Update
     affected current-behavior claims with each task. Remove this section when no plans remain. -->

## Cross-cutting concerns

- **Auth:** {approach}
- **Errors:** {approach}
- **Observability:** {logs/metrics/traces — see docs/runbook.md}
- **Config/secrets:** {approach}

## Decisions affecting this architecture

<!-- Link the ADRs that shaped the above. -->

- [ADR-0001](./adr/0001-record-architecture-decisions.md)
