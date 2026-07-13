# Walkthroughs

Two runs of the same pipeline: a new project and an existing one. The only difference is the
on-ramp (Stage 0).

---

## A. New project (greenfield) — "TenantPay"

**Stage 0a — Context (bootstrap).** Agent scaffolds `AGENTS.md` and fills `docs/context.md`
(domain: landlords, tenants, online rent payments, identity verification (KYC); glossary; constraints). No code yet.
→ gate: context filled (STATUS marker removed).

**Stage 0b — Foundation.** Agent writes the **project-level** artifacts: `docs/prd/0000-product.md`
(vision: in-app rent payments + verified listings), the foundational ADRs (`0002-stack`,
`0003-postgres-datastore`, `0004-cookie-auth`, `0005-rest-openapi`) in `docs/adr/`, a skeleton
`docs/architecture.md` (React web + Node API + Postgres), and a core `api/openapi.yaml` scaffold
(with `docs/contracts/README.md` trimmed to the real paths). → **GATE: approve foundation.**
(Per-feature ADRs/contracts come later, not here.)

**Stage 1 — Spec.** Discovery → PRD → stress-test, in one movement:

- `brainstorming` (**method only**): you say "tenants should pay rent online"; the agent
  explores **one question at a time** and lands a brief at `docs/briefs/0001-rent-payment.md`
  (problem, users, success metric: ≥80% of rent paid in-app within 2 months). Discovery is
  exploratory — **no code**, and it does **not** jump to `writing-plans`.
- `to-prd`: brief → `docs/prd/0001-rent-payment.md`.
- `grill-me`: hardens it — partial payments? failed payment callback? refunds?

→ **GATE: approve PRD.** (No GitHub issues yet — those come at Decompose.)

**Stage 2 — Architecture + Contract.** `docs/adr/0006-payment-provider-abstraction.md` ("wrap
providers behind one interface; why vs. direct integration"); `architecture.md` gains a payments
component; `docs/security.md` gets a threat model (payments + PII). The contract `api/openapi.yaml`
gains `POST /payments`, `GET /payments/:id`, and webhook `POST /payments/callback`; Zod schemas
generate TS types. → **GATE: approve approach + freeze interface.** Now FE and BE build in parallel.

**Stage 3 — Decompose.** `writing-plans`: PRD → 6 **GitHub issues** (the tracker is the record —
no in-repo mirror). `project-status` reports the breakdown; agent discloses it and continues (no gate).

**Stage 4 — Implement.** `feature-start` opens the branch `feat/3-payment-intent`, loads the
PRD/ADR/contract, enters plan mode. → **GATE per task.** Code written against the frozen contract;
`frontend-design` for the pay screen.

**Stage 5 — QA** (`test-driven-development`, `webapp-testing`, `run`/`verify`). Tests green and CI
green; agent runs the app and completes a sandbox payment.

**Stage 6 — Review.** Inline, no separate gate: `code-review` + `simplify`, and — because this
touches payments + PII — `security-review` (**mandatory** for sensitive areas). Findings fixed.

**Stage 7 — Land.** Agent opens the PR referencing the issue (`Closes #N`); merging closes it on
the tracker — no in-repo mirror to update.
→ **GATE: you merge.** Merge is always the human's call.

**Stage 8 — Retro.** Learnings ("payment callbacks can arrive twice — make handlers
idempotent") appended to `docs/context.md` (and, optionally, agent memory).

---

## B. Existing project — adopting the workflow

**Stage 0 — adopt** (`improve-codebase-architecture`). Agent reverse-engineers `docs/context.md`
and `docs/architecture.md` *from the code*, and backfills a few lightweight ADRs for decisions
already baked in (e.g. `0002-monorepo-with-pnpm.md`, status: Accepted, "recorded retroactively").
Adds `AGENTS.md` and points `docs/contracts/README.md` at the contract source that already exists.
**No behavior change** — this is documentation only. → review & approve.

**Stages 1–8 — identical.** The next feature enters at Spec and flows through the same gates.
Existing code just means Stage 2 *amends* `architecture.md` and *extends* an existing contract
instead of starting one (changing a shipped contract endpoint triggers a versioning ADR).

---

## What the gates feel like

At each ✅ the agent stops and says, e.g.: *"PRD ready at `docs/prd/0001-rent-payment.md`,
open questions resolved. Approve to proceed to architecture + contract, or tell me what to
change."* Nothing downstream happens until you respond.

Between gates — Decompose, QA, Review — the agent **proceeds and discloses**: it does the work,
tells you what it did and any decision you might want to override, and keeps moving. You can
interrupt at any time; it doesn't wait.
