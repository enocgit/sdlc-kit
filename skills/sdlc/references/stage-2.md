# Stage 2 — Architecture and Contract

Read this before any Stage 2 work. Gate mechanics live in the router; the landing ask forms are
restated below (`references/rules.md` stays canonical).

## Output

- ADRs in `docs/adr/NNNN-{slug}.md` — but only for choices that are **hard to reverse or constrain
  later decisions** (a shipped contract with consumers, an identity model, a datastore choice, a
  security boundary). A choice a later feature can cheaply change is recorded in the PRD's Key
  decisions instead; an ADR per feature by default is over-documentation. Use the kit's ADR
  template; never write to `docs/decisions/`.
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

Freeze a contract only when some consumer cannot be updated inside the same change: another
repository, a published package, another service or client, or a team you don't ship with.
Interfaces consumed only within this change stay unfrozen — keep tests in sync instead. Stage 0
recorded the outside-consumer fact in `docs/context.md`; read it rather than guessing at org
structure.

A frozen interface is never allowed to drift from implementation. A shipped contract with a
deployed consumer requires a versioning/deprecation ADR (`AGENTS.md` → Guardrails); with no
deployed consumer, apply the ADR matrix and re-freeze.

## Gate

**GATE — approve spec + approach (+ freeze interface).** For a contract-free feature this one
approval covers the full Stage 1–2 package — PRD, ADRs, architecture and security updates; the
PRD did not stop at its own gate. A feature that freezes a contract keeps the separate Stage 1
PRD gate, and this gate approves the approach and the freeze. At this gate, ask to land the
planning package on `main` before decomposition. Landing ask, by remote state:

- **No remote** → commit to the local default branch.
- **Remote, default branch unprotected** → commit and push it under the same approval, so the
  shared default branch holds the frozen contract.
- **Remote, default branch protected** → `plan/{NNNN}-{slug}` → PR → merge, then branch `feat/*`
  from the merged ref; wait for the human to confirm the package reached the default branch.

Stage 4 cuts `feat/*` from a ref that must already hold the frozen contract. A commit alone on an
unprotected remote leaves Stage 4 branching from a base the remote lacks, folding the planning
package into the feature PR.

Before asking to land a package that touches a sensitive area, update `docs/security.md` and run
`security-review` on the planning diff with the coverage check in `references/rules.md`. Stage 6
reviews the implementation diff separately.

## Next

After this stage's gate approval or proceed-disclosure, announce Stage 3 and read
`references/stage-3.md` before acting on it — the skill alone is not the procedure.
