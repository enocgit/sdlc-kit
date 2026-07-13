# Security & threat model

> Lightweight, living security doc. Touched at the **Architecture** stage for any feature in a
> **sensitive area** (canonical list in `AGENTS.md` → Sensitive areas), and revisited at review.
> Not a formal audit — a structured "what could go wrong and how do we prevent it."

## Threat model (per sensitive feature)

For each feature, capture briefly:

| Asset / data | Threat | Mitigation | Owner |
|--------------|--------|------------|-------|
| {e.g. payment token} | {e.g. replay / interception} | {e.g. idempotency key, TLS, signed webhook} | {who} |

Prompts to answer: Who are the actors (incl. malicious)? What data is sensitive? What's the
trust boundary? What happens if each input is hostile? What if a dependency/webhook lies?

## Baseline controls (check on every sensitive change)

- [ ] **AuthN/AuthZ** — every endpoint checks identity *and* permission; no broken object-level
      access (can user A read user B's data?)
- [ ] **Input validation** — all inputs validated against the contract schema; output encoded
- [ ] **Secrets** — never in code/logs; loaded from env/secret manager; rotation possible
- [ ] **PII/KYC** — minimized, encrypted at rest where required, access logged
- [ ] **Payments** — idempotent handlers, signed/verified webhooks, no trust of client amounts
- [ ] **Transport** — TLS everywhere; secure cookies; CORS locked down
- [ ] **Dependencies** — no known-vulnerable packages (CI advisory scan)
- [ ] **Rate limiting / abuse** — on auth, payment, and enumeration-prone endpoints
- [ ] **Logging** — security events logged; no secrets/PII in logs

## Review

`security-review` runs at Review (Stage 6), before the Stage 7 merge, for any change in a
sensitive area and must close its findings — this is mandatory, not agent-discretion. Decisions
that change the security posture are recorded as ADRs.
