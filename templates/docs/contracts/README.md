# Contracts

> The integration **source of truth** between frontend, backend, and services. Contracts are
> *artifacts, not prose* — they live in the codebase and (ideally) generate the types both sides
> consume, so the contract can't silently drift from the code. This folder documents where they
> live and the rules around them.

## Where the contract artifacts live

> **REPLACE THIS LIST at Stage 0.** The entries below are *examples*, not real locations. At
> foundation (0b), once the API-style/datastore ADRs are decided, delete what doesn't apply and
> point each remaining line at a path that **actually exists in this repo** (or mark it
> `(future — not built yet)`). Leaving template paths here sends implementers and agents to
> non-existent files and breaks the contract-first handoff.

- **HTTP API:** `api/openapi.yaml` (OpenAPI) — generates client + server types.
- **RPC:** tRPC routers in `packages/api/src/routers/*` — types shared directly.
- **Validation:** Zod schemas in `packages/contracts/*` — single source for runtime + types.
- **Database:** `prisma/schema.prisma` + `prisma/migrations/*`.
- **Events/messages:** `contracts/events/*.json` (JSON Schema / Avro).

## The contract-first rule

1. Define/extend the contract **before** implementing (Stage 2).
2. **Freeze** it at the gate — then FE and BE implement against it in parallel.
3. Generate types from the contract; never hand-duplicate them on each side.
4. Changing a **shipped** contract endpoint/field is a decision: write a new ADR covering
   versioning/deprecation and backward compatibility. No silent breaking changes.

## Checklist when adding/changing a contract

- [ ] Request/response shapes + error cases specified
- [ ] Validation rules (required, formats, limits)
- [ ] Auth/permission requirements per endpoint
- [ ] Pagination/filtering conventions followed
- [ ] Backward compatibility considered (and ADR if breaking)
- [ ] Types regenerated; both sides compile
