# Workflow example

This example follows TenantPay, a new rental-payment product, through the full workflow. Backticks
mark skills, paths, branches, and commands.

## New project: TenantPay

TenantPay lets tenants pay rent online through verified property listings.

### 0a. Fill context

The agent records TenantPay's users, domain terms, and constraints in `docs/context.md`. No feature
code exists yet.

**Gate:** the context is filled. The agent stops before foundation work.

### 0b. Establish the foundation

The agent creates the product requirements document (PRD), foundational architecture decision
records (ADRs), architecture skeleton, core contract, and threat model. It replaces the test
strategy's placeholder runners with TenantPay's real tools. Authentication is sensitive, so it runs
`security-review` on this planning diff.

**Gate:** approve the foundation and land the context-and-foundation package on `main` — the commit,
and the push when a remote's `main` is unprotected. If `main` is protected, use a `plan/*` pull
request (PR) and wait for the human to merge it.

### 1. Write the feature specification

The user says, "Tenants should pay rent online." `brainstorming` asks one question at a time and
records an optional brief. `to-spec` turns the result into
`docs/prd/0001-rent-payment.md`. `grilling` resolves partial payments, failed callbacks, and refunds.

**Gate:** approve the feature PRD. No tracker tasks exist yet.

### 2. Choose the architecture and freeze the contract

The agent records the payment-provider decision in an ADR, adds the payment component to
`docs/architecture.md`, and threat-models payments and personally identifiable information (PII) in
`docs/security.md`. For TenantPay, the contract lives in `api/openapi.yaml`; the agent generates
shared types from it. Other projects can freeze tRPC routers, ts-rest contracts, schemas, or interface
definitions instead.

`grilling` stress-tests the architecture and the contract shape before the agent freezes either, so
the interface is challenged while it is still cheap to change.

The agent runs `security-review` on this sensitive planning diff. Stage 6 reviews the implementation
diff separately.

**Gate:** approve the approach, freeze the interface, and land the Stage 1–2 planning package on
`main` — the commit, and the push when a remote's `main` is unprotected, so the shared `main` holds
the contract. If `main` is protected, use a `plan/*` PR and wait for the human to merge it. Frontend
and backend can then work against the same contract.

### 3. Break the feature into tasks

`writing-plans` turns the PRD into tracker tasks. `project-status` reports the breakdown. The agent
discloses it and continues without waiting for another approval.

### 4. Implement a task

`feature-start` creates `feat/3-payment-intent` and loads the relevant PRD, ADR, and contract.

**Gate:** approve the compact in-session task plan. The agent creates no plan file unless the human
asks for one. After approval, it implements against the frozen contract.

### 5. Verify the change

The agent runs tests, starts the app, and completes a sandbox payment. Continuous integration (CI)
runs before Land when possible. If the project needs a PR to start CI, Land opens it first.

### 6. Review the diff

`code-review` and `simplify` inspect the diff. Because the feature touches payments and PII, the
agent also runs `security-review` and fixes its findings. `definition-of-done-review` confirms local
readiness. Required CI is the only pending item before Land.

### 7. Land the change

After local review, the agent asks for one approval to commit, push, and open the PR. The request
must name those actions; it never authorizes merge. The GitHub PR uses `Closes #N`, and the issue
stays open until merge.

After required CI passes, the agent runs the final Definition of Done check and reports whether the
change is ready to merge.

**Gate:** the human merges after CI is green and the final check passes. GitHub then closes the issue.

### 8. Record what was learned

After each task, the agent keeps only durable learnings, such as "payment callbacks may arrive twice;
handlers must be idempotent." If tasks remain, it leaves feature artifacts and the epic checklist
alone. If it records a durable learning in a project file, it checks out and syncs the updated default
branch before editing, then asks to land that change before the next task. If no repository file
changed, there is no extra landing action.

After the final task, the agent checks out and syncs the updated default branch before reconciling
feature artifacts, including the frozen contract and contract index, and updating statuses. It asks
for approval to land those edits. After they land, it verifies the epic Definition of Done and asks
for approval to update and close the parent GitHub issue. After that approval and verified closure,
it offers the optional `improve` audit, `improve next`, or the next `sdlc {feature}` run.

## Existing project

The `adopt` path changes only Stage 0. The agent reads the code, configures `docs/test-strategy.md`,
and reconstructs `docs/context.md`, `docs/architecture.md`, contract pointers, and retrospective
ADRs. It documents existing behavior without changing it.

After foundation approval, the next feature follows Stages 1–8. Extend existing architecture and
contracts instead of creating duplicates. A shipped-contract change requires a versioning or
deprecation ADR.

## Gate behavior

At every gate, the agent names the artifact and asks for approval. It does nothing downstream until
the human responds. At other stages, it works, reports decisions worth changing, and continues. The
human can interrupt at any time and always controls merge.
