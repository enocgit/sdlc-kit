# Workflow example

TenantPay lets tenants pay rent online through verified property listings. This follows it from an
empty repository to its first shipped feature. Backticks mark skills, paths, and commands.

## 0. Foundation

The agent fills `docs/context.md`: product, Lifecycle (`team`, no deployed consumers, no real data,
no traffic), the mobile client as an outside consumer, and two hard constraints. It lists the areas
`auth` and `payments` in `docs/specs/README.md`, writes ADRs for the stack, the datastore, and the
auth model, and sketches `docs/architecture.md`, `docs/security.md`, and `docs/test-strategy.md`.

It sets `pnpm check` as the check command and wires it into CI. Then it plants a type error, a
failing test, and a lint violation one at a time, sees `pnpm check` fail at each part, and reverts
each.

**Gate:** approve the foundation. With a protected `main`, it lands through a `plan/0000-foundation`
PR.

## 1. Plan

The user says, "Tenants should pay rent online." `grilling` asks in rounds, each question with a
recommended answer, and settles partial payments, failed callbacks, and refunds.

The agent writes `docs/changes/0001-rent-payment.md` (62 lines): the spec delta adds `PAY-1` to
`PAY-4`, five acceptance criteria, the provider ADR, and the frozen `api/openapi.yaml` slice the
mobile client needs. Payments move a trust boundary, so the threat delta is in the proposal and
`security-review` runs on it before the gate.

**Gate:** approve the plan. The team shape lands it on `main` before any branch is cut.

## 2. Decompose

Three GitHub issues under an epic, each one reviewable PR: the payment record and provider client,
the webhook handler, and the tenant payment screen. Each lists its acceptance criteria with
requirement IDs and test layers. The agent discloses the order and continues.

## 3. Build

For the webhook task the agent branches `feat/12-payment-webhook`. Because the task is sensitive, it
stops for approval of its short plan. It writes `PAY-3 rejects an unsigned webhook` as an
integration test against the test database, sees it fail, and implements the handler. It moves
`PAY-3` into `docs/specs/payments.md` and updates the webhook row in `docs/security.md` in the same
commit.

## 4. Review

A fresh subagent receives the diff, the proposal, the payments spec, and the contract. `code-review`
asks for one change: the handler retries on every error, including a bad signature.
`security-review` records two findings in a 24-line record. It fixes one; the other, rate limiting the
webhook endpoint, goes to the production register until there is production traffic. After the fix,
a second round approves.

## 5. Land

The agent pushes and opens the PR. "Where to look" points at the signature check and the idempotency
key, and the proof table maps each criterion to its test. It reports the PR link and that CI is
running, then stops. The human merges after CI passes.

## 6. Retro

GitHub closes the issue. The first merged CI run's log shows lint, typecheck, and all tests ran,
matching the local count. One learning qualifies: the provider sends webhook timestamps in seconds, not
milliseconds. When the third task merges, the agent checks the payments spec against the code and
marks the proposal Shipped with links to its three PRs.
