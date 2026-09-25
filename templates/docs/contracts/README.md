# Contracts

> Follow the documentation writing standard in AGENTS.md. Keep contract docs precise and
> scan-first: authoritative paths, request/response shape, auth, validation, errors, compatibility,
> and freeze status before examples or extended notes.
>
> Contracts are the integration **source of truth** between frontend, backend, and services.
> They are _artifacts, not prose_: they live in the codebase and provide the types both sides
> consume, either by generating them or sharing them directly. This reduces structural drift from
> the code. This folder documents where they live and the rules around them.

## Where the contract artifacts live

> **Replace this list before the project begins implementation.** The entries below are _examples_,
> not real locations. Delete what does not apply and point each remaining line at a path that
> **actually exists in this repo** (or mark it `(future — not built yet)`). Leaving template paths
> here sends implementers and agents to non-existent files and breaks the contract-first handoff.

- **HTTP API:** `api/openapi.yaml` (OpenAPI) — generates client + server types.
- **RPC:** tRPC routers in `packages/api/src/routers/*` — types shared directly.
- **Validation:** Zod schemas in `packages/contracts/*` — single source for runtime + types.
- **Database:** `prisma/schema.prisma` + `prisma/migrations/*`.
- **Events/messages:** `contracts/events/*.json` (JSON Schema / Avro).
- **Boundary documents:** when an interface needs prose beyond schemas (auth wire protocols,
  callback flows), a contract document may live in this folder next to the pointers — keep it
  scan-first and link it from the list above.

## The contract-first rule

1. Define or extend the contract **before** implementation.
2. **Freeze** it before consumers implement against it.
3. Generate types from the contract or share contract-defined types directly; never hand-duplicate
   them on each side.
4. Changing a **shipped** contract endpoint/field with a deployed consumer is a decision: write a
   new ADR covering versioning/deprecation and backward compatibility. No silent breaking changes.
   With no deployed consumer, compatibility versioning can be deferred: change the contract outright
   only under the ADR matrix, with applicable human approval and a re-freeze, and record the deferral
   in the production register in `docs/context.md`.

## Checklist when adding/changing a contract

- [ ] Request/response shapes + error cases specified
- [ ] Validation rules (required, formats, limits)
- [ ] Auth/permission requirements per endpoint
- [ ] Pagination/filtering conventions followed
- [ ] Backward compatibility considered (and ADR if breaking)
- [ ] Types regenerated or shared directly from the contract; both sides compile
