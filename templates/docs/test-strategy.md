# Test strategy

> Follow the documentation writing standard in AGENTS.md. Keep this doc focused on test-specific
> policy and links to real tools; do not duplicate the canonical Definition of Done from AGENTS.md.
> Delete placeholder runners once the stack is set.
>
> **STATUS: TEMPLATE** — set the tools below from your **real** stack; the tool names are
> placeholders, not a decision (e.g. the starter may be wired for Jest, not Vitest). The
> authoritative completion policy lives in the project's operating manual. This doc adds only the
> test-specific bar (see "Verification bar" below).

## Policy

Every task needs verification evidence; not every change needs a new automated test. For bug fixes
and non-trivial testable behavior, begin with a failing test and follow a RED → GREEN cycle.
Otherwise choose the smallest check that proves the change: existing tests, typecheck, build,
schema validation, dry-run, smoke test, browser observation, or another concrete oracle. When
adding no test, state why it would add little confidence and record the alternative evidence.

## Test layers (the pyramid)

| Layer | Tool | What it covers | When required |
| ------- | ------ | ---------------- | --------------- |
| Unit | {unit runner — e.g. Vitest or Jest} | Pure logic, edge cases | All non-trivial logic |
| Integration | {same runner} + test DB | Module ↔ DB, API handlers against the contract | Any data/contract change |
| Contract | (contract-defined types, generated or directly shared) + schema validation | FE/BE agree on the frozen interface | Any contract change |
| E2E | {e2e tool — e.g. Playwright, Cypress, Maestro, or Detox} | Critical user flows end-to-end | Per epic's key flow |

**Rule of thumb:** test logic at the lowest layer that gives confidence; reserve E2E for the few
flows that matter most. Non-trivial behavior must be _covered_, not merely _touched_. Styling,
documentation, configuration, generated output, and already-covered refactors may use more direct
evidence when an additional automated test would not improve confidence.

## Verification bar

The project's operating manual defines the broader completion policy. This document adds only the
test-specific bar: proportional verification per the policy above, automated coverage for non-trivial
behavior at the **right layer**, and the existing suite fully green.

## Conventions

- Deterministic tests (no real network/time/randomness without control).
- Test names describe behavior, not implementation.
- A bug fix starts with a failing test that reproduces it (RED → GREEN).
