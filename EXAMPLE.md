# Workflow example

This walkthrough follows a new project through the full pipeline, then shows how adoption differs
for an existing codebase.

## New project: TenantPay

The idea: let tenants pay rent online through verified property listings.

### 0a. Context

The agent fills `docs/context.md` with users, domain terms, and constraints. No feature code exists
yet.

**Gate:** context filled. The agent waits before starting foundation work.

### 0b. Foundation

The agent creates the project PRD, foundational ADRs, architecture skeleton, and core contract.

**Gate:** approve the foundation.

### 1. Spec

The user starts with “tenants should pay rent online.” `brainstorming` resolves one question at a
time and records an optional brief. `to-prd` turns it into `docs/prd/0001-rent-payment.md`.
`grill-me` resolves cases such as partial payments, failed callbacks, and refunds.

**Gate:** approve the feature PRD. No tracker issues exist yet.

### 2. Architecture and contract

The agent records the payment-provider decision in an ADR, adds the payment component to
`docs/architecture.md`, and threat-models payments and PII in `docs/security.md`. For TenantPay, it
defines payment and webhook endpoints in `api/openapi.yaml` and generates shared types. Other
projects freeze their actual contract source, such as tRPC routers, ts-rest contracts, schemas, or
interface definitions.

**Gate:** approve the approach and freeze the interface. Frontend and backend can now work against
the same contract.

### 3. Decompose

`writing-plans` converts the PRD into tracker issues. `project-status` reports the breakdown. The
agent discloses it and continues without waiting.

### 4. Implement

`feature-start` creates `feat/3-payment-intent` and loads the relevant PRD, ADR, and contract.

**Gate:** approve the task plan. The agent implements against the frozen contract.

### 5. QA

The agent runs tests, starts the app, completes a sandbox payment, and confirms CI is green.

### 6. Review

`code-review` and `simplify` inspect the diff. Because the feature touches payments and PII, the
agent also runs `security-review` and fixes its findings.

### 7. Land

The agent opens a GitHub PR with `Closes #N`. The issue remains open while the PR is under review.

**Gate:** the human merges. GitHub then closes the issue.

### 8. Retro

The agent prunes stale context and adds up to three durable learnings, such as “payment callbacks
may arrive twice; handlers must be idempotent.” It then offers the optional `improve` audit,
`improve next`, or the next `sdlc {feature}` run.

## Existing project

The `adopt` path changes only Stage 0. The agent reads the code and reconstructs
`docs/context.md`, `docs/architecture.md`, contract pointers, and a few retrospective ADRs. This
step documents existing behavior; it does not change it.

After foundation approval, the next feature follows Stages 1–8 above. Architecture and contracts
are extended instead of created. Changing a shipped contract requires a versioning or deprecation
ADR.

## Gate behavior

At each gate, the agent names the completed artifact and asks for approval. It does nothing
downstream until the human responds. At non-gate stages, it performs the work, reports decisions
worth overriding, and continues. The human can interrupt at any time and always controls merge.
