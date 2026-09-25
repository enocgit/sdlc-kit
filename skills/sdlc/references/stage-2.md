# Stage 2 — Architecture and Contract

Read this before any Stage 2 work. Gate mechanics live in the router; landing mechanics in
`references/rules.md`.

## Output

- ADR(s) in `docs/adr/NNNN-{slug}.md` for the decisions this feature makes (use the kit's ADR
  template; never write to `docs/decisions/`).
- Updated `docs/architecture.md` — current system shape.
- Updated `docs/security.md` when the feature touches a sensitive area: extend the threat model.
- The **frozen** contract artifact in the repo: `api/openapi.yaml`, tRPC routers, `schema.prisma`,
  Zod schemas, or the project's equivalent — indexed in `docs/contracts/README.md`.

## Skills

- `documentation-and-adrs` — ADRs go to `docs/adr/NNNN-{slug}.md` (this project's convention).
- `grilling` — stress-tests the architecture and the contract shape **before** the freeze, so the
  interface is challenged while it is still cheap to change. Point it at the decision, not the
  document.

## Artifact lifecycle (apply here and throughout)

- Approved future changes go in a separate planned-changes section of architecture and security
  docs; do not rewrite the current system as though the design were implemented.
- PRD approval, ADR acceptance, and contract freeze are decision states; they live in their
  artifacts. Live implementation state lives only in the tracker. No intermediate status prose
  anywhere — a claim is written when it is true, at final reconciliation
  (`references/stage-8.md`).
- Compatibility artifacts, deprecation notes, and migration guidance in current-state docs describe
  an active transition someone has to make; use the specific Lifecycle trigger in `docs/context.md`.

## Contract-first

Define and freeze the interface before parallel FE/BE implementation. Never let implementation
drift from the frozen contract. A shipped contract with a deployed consumer requires a
versioning/deprecation ADR (`AGENTS.md` → Guardrails); with no deployed consumer, apply the ADR
matrix and re-freeze.

## Gate

**GATE — approve approach + freeze interface.** At this gate, ask to land the full Stage 1–2
planning package (PRD, ADRs, architecture and security updates, frozen contract) on `main` before
decomposition, using the remote-state landing action in `references/rules.md` → Default-branch
landings. Stage 4 cuts `feat/*` from a ref that must already hold the frozen contract.

Before asking to land a package that touches a sensitive area, update `docs/security.md` and run
`security-review` on the planning diff with the coverage check in `references/rules.md`. Stage 6
reviews the implementation diff separately.
