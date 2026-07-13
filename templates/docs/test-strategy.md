# Test strategy & Definition of Done

> **STATUS: TEMPLATE** — set the tools below at Stage 0 from your **real** stack; the tool names
> are placeholders, not a decision (e.g. the starter may be wired for Jest, not Vitest). The
> authoritative **Definition of Done** and **Definition of Ready** live in `AGENTS.md` and are
> enforced before Land; this doc only adds the test-specific bar (see "Definition of Done" below).

## Test layers (the pyramid)

| Layer | Tool | What it covers | When required |
|-------|------|----------------|---------------|
| Unit | {unit runner — e.g. Vitest or Jest} | Pure logic, edge cases | All non-trivial logic |
| Integration | {same runner} + test DB | Module ↔ DB, API handlers against the contract | Any data/contract change |
| Contract | (generated types) + schema validation | FE/BE agree on the frozen interface | Any contract change |
| E2E | {e2e tool — e.g. Playwright or Cypress} | Critical user flows end-to-end | Per epic's key flow |

**Rule of thumb:** test logic at the lowest layer that gives confidence; reserve E2E for the
few flows that matter most. New logic must be *covered*, not merely *touched*.

## Definition of Done

The **canonical Definition of Done lives in `AGENTS.md`** ("Definition of Done") — one list, no
copies to drift; `definition-of-done-review` checks against it at the merge gate. What this
document adds to that bar: tests at the **right layer** per the table above, the suite fully
green, and the change **run and observed working** (`run`/`verify`) — with `security-review` when
a sensitive area is touched (canonical list in `AGENTS.md` → Sensitive areas).

## Conventions

- Deterministic tests (no real network/time/randomness without control).
- Test names describe behavior, not implementation.
- A bug fix starts with a failing test that reproduces it (RED → GREEN).
