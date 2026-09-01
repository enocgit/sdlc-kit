# Security & threat model

> Follow the documentation writing standard in AGENTS.md. Keep each threat model scan-first:
> invariants, actors, trust boundaries, then a compact threat table. Move long explanations below
> the table or into ADRs.
>
> Lightweight, living security doc. At **Foundation**, replace the example row with project-specific
> threats for foundational auth and other sensitive surfaces. Update it at **Architecture** for each
> sensitive feature (canonical list in `AGENTS.md` → Sensitive areas), then revisit it at review.
> Not a formal audit — a structured "what could go wrong and how do we prevent it."

## Threat model (per sensitive feature)

For each feature, capture briefly:

| Asset / data | Threat | Mitigation | Owner |
|--------------|--------|------------|-------|
| {e.g. payment token} | {e.g. replay / interception} | {e.g. idempotency key, TLS, signed webhook} | {who} |

Prompts to answer: Who are the actors (incl. malicious)? What data is sensitive? What's the
trust boundary? What happens if each input is hostile? What if a dependency/webhook lies?

## Baseline controls (check on every sensitive change)

- [ ] **AuthN/AuthZ** — every endpoint checks identity _and_ permission; no broken object-level
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

Run `security-review` before landing a sensitive Foundation or Architecture planning package, and
again at Review (Stage 6) for the implementation diff. Close all findings before each merge; this
is mandatory, not agent discretion. Record decisions that change the security posture as ADRs.
