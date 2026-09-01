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

The agent creates the project PRD, foundational ADRs, architecture skeleton, core contract, and
foundational threat model, then replaces the test strategy's placeholder runners with the project's
real tools. Because authentication is sensitive, it runs `security-review` on this planning diff.

**Gate:** approve the foundation and land the context + foundation package on `main`. If `main` is
protected, use a `plan/*` PR and wait for the human to merge it.

### 1. Spec

The user starts with “tenants should pay rent online.” `brainstorming` resolves one question at a
time and records an optional brief. `to-prd` turns it into `docs/prd/0001-rent-payment.md`.
`grilling` resolves cases such as partial payments, failed callbacks, and refunds.

**Gate:** approve the feature PRD. No tracker issues exist yet.

### 2. Architecture and contract

The agent records the payment-provider decision in an ADR, adds the payment component to
`docs/architecture.md`, and threat-models payments and PII in `docs/security.md`. For TenantPay, it
defines payment and webhook endpoints in `api/openapi.yaml` and generates shared types. Other
projects freeze their actual contract source, such as tRPC routers, ts-rest contracts, schemas, or
interface definitions. It runs `security-review` on the sensitive planning diff before landing it;
Stage 6 reviews the implementation diff separately.

**Gate:** approve the approach, freeze the interface, and land the Stage 1–2 planning package on
`main`. If `main` is protected, use a `plan/*` PR and wait for the human to merge it. Frontend and
backend can then work against the same contract.

### 3. Decompose

`writing-plans` converts the PRD into tracker issues. `project-status` reports the breakdown. The
agent discloses it and continues without waiting.

### 4. Implement

`feature-start` creates `feat/3-payment-intent` and loads the relevant PRD, ADR, and contract.

**Gate:** approve the compact in-session task plan. No plan file is created unless the human asks
for one. The agent then implements against the frozen contract.

### 5. QA

The agent runs tests, starts the app, and completes a sandbox payment. CI is green when it can run
before a PR; otherwise it remains pending until Land opens the PR.

### 6. Review

`code-review` and `simplify` inspect the diff. Because the feature touches payments and PII, the
agent also runs `security-review` and fixes its findings. It then runs the mandatory local-readiness
`definition-of-done-review`; required CI is the only pending item before Land.

### 7. Land

After local review, the agent asks for one combined approval to commit, push, and open the PR. The
request authorizes only those named actions, never merge. The GitHub PR uses `Closes #N`; the issue
remains open while the PR is under review. After required CI passes, the agent runs the final DoD
confirmation and reports whether the change is ready to merge.

**Gate:** the human merges after CI is green and final DoD confirmation passes. GitHub then closes
the issue.

### 8. Retro

After every task, the agent curates only durable learnings, such as “payment callbacks may arrive
twice; handlers must be idempotent.” If the epic has unfinished tasks, it leaves feature artifacts
and the epic checklist alone. A real learning is landed on the updated default branch before the
next task; when no repository file changed, there is no extra landing action. After the final task,
the agent reconciles and lands feature artifacts and statuses, verifies the epic DoD, and only then
asks to update and close the parent GitHub issue. Once the parent is closed, it offers the optional
`improve` audit, `improve next`, or the next `sdlc {feature}` run.

## Existing project

The `adopt` path changes only Stage 0. The agent reads the code, configures
`docs/test-strategy.md`, and reconstructs `docs/context.md`, `docs/architecture.md`, contract
pointers, and a few retrospective ADRs. This step documents existing behavior; it does not change
it.

After foundation approval, the next feature follows Stages 1–8 above. Architecture and contracts
are extended instead of created. Changing a shipped contract requires a versioning or deprecation
ADR.

## Gate behavior

At each gate, the agent names the completed artifact and asks for approval. It does nothing
downstream until the human responds. At non-gate stages, it performs the work, reports decisions
worth overriding, and continues. The human can interrupt at any time and always controls merge.
