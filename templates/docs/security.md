# Security & threat model

> Follow the documentation writing standard in AGENTS.md. Keep each threat model scan-first:
> invariants, actors, trust boundaries, then a compact threat table. Move long explanations below
> the table or into ADRs.
>
> Lightweight, living security doc. Replace the example row with project-specific threats for
> foundational authentication and other sensitive surfaces. Update it when a sensitive feature or
> trust boundary changes, then revisit it during review. This is not a formal audit; it is a
> structured record of what could go wrong and how the system prevents it.

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

## Review record

- **Scope / date:** {scope} / YYYY-MM-DD
- **Findings:** {finding summary, or None}
- **Resolutions:** {how findings were addressed}
- **Residual risks / owners:** {remaining risk, owner, and follow-up, or None}
- **Related ADRs:** {links, or None}
