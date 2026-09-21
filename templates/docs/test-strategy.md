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

Every task needs verification evidence; not every change needs a new automated test. For bug fixes, use a failing automated test or observable reproducer appropriate to the risk. For
non-trivial executable behavior, begin with a failing test and follow a RED → GREEN cycle.
Otherwise name the smallest check that proves the change: existing tests, typecheck, build, schema
validation, dry-run, smoke test, rendered-output inspection, or another concrete oracle. Presentation-only
styling, markup, attributes, copy, and layout may use a diff or one visual check; styling, markup, or
attributes that change accessibility, security, or interaction behavior need focused behavior evidence.
This is the local evidence bar; do not duplicate the full CI suite by default. A full configured suite
is a merge gate when CI exists, not a local pre-PR requirement.

The Lifecycle block in `docs/context.md` sets the reach of this bar. While it shows nothing deployed,
no real data, and no traffic, cover executable non-trivial logic, including validation, authorization
or security denial, error, retry, timeout, and partial-failure branches. Defer only cases whose
required deployed consumer, real data, deployment, load, traffic, compatibility, or multi-version
condition is unavailable. Record each skipped case in the production register instead of writing the
test.

## Test layers (the pyramid)

| Layer | Tool | What it covers | When required |
| ------- | ------ | ---------------- | --------------- |
| Unit | {unit runner — e.g. Vitest or Jest} | Pure logic, edge cases | All non-trivial logic |
| Integration | {same runner} + test DB | Module ↔ DB, API handlers against the contract | Any data/contract change |
| Contract | (contract-defined types, generated or directly shared) + schema validation | FE/BE agree on the frozen interface | Any contract change |
| Failure path | {same runner} | Validation, authorization or security denial, error, retry, timeout, and partial-failure behavior | Whenever the executable branch can be exercised; defer only cases whose required deployed consumer, real data, deployment, traffic, load, compatibility, or multi-version condition is unavailable; see Lifecycle |
| Load / perf | {tool} | Throughput, latency, saturation | When staging or production traffic exists |
| E2E | {e2e tool — e.g. Playwright, Cypress, Maestro, or Detox} | Critical user flows end-to-end | Per epic's key flow |

**Rule of thumb:** test logic at the lowest layer that gives confidence; reserve E2E for the few
flows that matter most. Non-trivial executable behavior must be _covered_, not merely _touched_.
Presentation-only styling, markup, or copy, documentation, configuration, generated output, and already-covered
refactors may use more direct evidence when an additional automated test would not improve confidence;
styling, markup, or attributes that change accessibility, security, or interaction behavior still need
focused evidence.

## Verification bar

The project's operating manual defines the broader completion policy. This document adds only the
test-specific bar: proportional local verification per the policy above, automated coverage for
non-trivial executable behavior at the **right layer**, and configured CI fully green before merge when a CI
workflow exists.

## Conventions

- Deterministic tests (no real network/time/randomness without control).
- Test names describe behavior, not implementation.
- A bug fix starts with a failing automated test or observable reproducer appropriate to its risk
  (RED → GREEN).
- A regression test earns its place by reproducing a failure that actually occurred. For an
  unobserved condition that cannot be exercised before deployment, name the behavior it would protect
  and put it in the production register instead of writing the test now. This exception does not
  cover executable validation, authorization, security denial, error, retry, timeout, or partial-failure
  branches.
- Name the invariant, not the history: no "previously failed" or incident narration in test names
  or comments.
