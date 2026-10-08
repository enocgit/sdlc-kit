# Test strategy

> STATUS: TEMPLATE — set the real tools at Stage 0 and delete this marker.

Test where a bug would surface. Mocks hide the behavior of databases, auth libraries, and frameworks,
which is where most real bugs live; unit tests are fastest for logic with many cases.

## Layers

| Code under test | Layer | Tool | Rule |
| --- | --- | --- | --- |
| Pure logic with many cases: policies, matrices, parsers, mappers | Unit | {runner} | One test per case; the full case matrix lives here |
| Wiring to the database, auth, HTTP, queues, or third parties | Integration, against real infrastructure | {runner} + {test database} | One test per path through the wiring, plus one denial and one failure or rollback; never the full matrix |
| Critical user journeys | End-to-end | {e2e tool} | A few per change, named in the change proposal |

A task's acceptance criteria name the layer for each behavior. Test names cite the requirement ID
they prove (`AUTH-3 rejects an expired session`); source comments don't repeat it.

## Execution

- Every new test is seen failing for the right reason before it passes.
- Tests are safe to run in parallel: each worker gets its own database or schema.
- Tests are deterministic: no uncontrolled network, time, or randomness.
- Test data carries the variation real inputs have (several users, empty and oversized values,
  messy formatting), not only the minimal case. A gap the real-world check finds becomes a test.
- Pull requests run the packages a change affects; the push to the default branch runs everything.
- No run repeats the same work: one workflow per check, and a new push cancels the PR's older run.
- One test runner per stack unless an ADR says otherwise.
- Locally, run the touched packages; CI is the merge gate.

## Deferred

Tests that need deployed consumers, real data, or production traffic wait in the production register
in `docs/context.md`. Executable validation, authorization, error, and failure branches are never
deferred.
