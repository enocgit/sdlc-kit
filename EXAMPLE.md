# Workflow example

TenantPay lets tenants pay rent online through verified property listings. This follows it from an
empty repository to its first shipped feature. Backticks mark skills, paths, and commands.

## Bootstrap

`bootstrap` fills `docs/context.md`: product, Lifecycle (`team`, no deployed consumers, no real
data, no traffic), the mobile client as an outside consumer, and two hard constraints. It lists the
areas `auth` and `payments` in `docs/specs/README.md`, writes ADRs for the stack, the datastore, and
the auth model, and sketches `docs/architecture.md`, `docs/threat-model.md`, and
`docs/test-strategy.md`.

It sets `pnpm check` as the check command and wires it into CI. Then it plants a type error, a
failing test, and a lint violation one at a time, sees `pnpm check` fail at each part, and reverts
each. **Gate:** the maintainer approves the foundation; with a protected `main`, it lands through a PR.

## Plan

The user says, "Tenants should pay rent online." `grilling` asks in rounds, each question with a
recommended answer, and settles partial payments, failed callbacks, and refunds.

The agent writes `docs/changes/0001-rent-payment.md`: the spec delta adds `PAY-1` to `PAY-4`, five
acceptance criteria, the provider ADR, and the frozen `api/openapi.yaml` slice the mobile client
needs. Its smoke check: in the provider's sandbox, a tenant pays a partial month's rent from the
payment screen and sees the remaining balance. Payments move a trust boundary, so the threat delta
is in the proposal and `security-review` runs on it. The proposal lists three slices: the payment
record and provider client, the webhook handler, and the payment screen.

**Gate:** the maintainer approves the plan, which also approves the three slice issues. The team shape
lands the proposal on `main` before any slice branches.

## Build

For the webhook slice the agent branches `feat/12-payment-webhook`. The slice is sensitive, so it
first says what it adds beyond the approved plan: nothing. It writes `PAY-3 rejects an unsigned
webhook` as an integration test against the test database, sees it fail, and implements the
handler. It moves `PAY-3` into `docs/specs/payments.md` and updates the webhook row in
`docs/threat-model.md` on the same branch. The smoke check runs later, with the payment-screen slice
that completes the flow.

## Review

The harness has no other model, but `codex exec` is installed, so the agent runs it with
`code-review` and `security-review`, the diff, the proposal, the payments spec, the contract, and the
raw check output. It asks for one change: the handler retries on every error, including a bad
signature. The security record has two findings: one fixed, and rate limiting the webhook goes to
the production register until there is production traffic. A second round on the new diff approves.

## PR and merge

The agent pushes and opens the PR. "Where to look" points at the signature check and the idempotency
key; the proof table maps each criterion to its test and names the reviewer and its model. It
reports the PR link and that CI is running, then stops. The maintainer merges after CI passes. When the
payment-screen PR lands, it carries the smoke check output and marks the proposal Shipped.
