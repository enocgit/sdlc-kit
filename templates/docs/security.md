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

For each feature, separate planned controls from currently enforced controls. Identify partial
implementation and link verification evidence. Approval or schema tests alone do not establish
runtime enforcement.
Update affected controls with each implementation change, not only when the feature finishes.

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

- **Scope / date:** {planning or implementation scope, intended file list} / YYYY-MM-DD
- **Reviewed identity:** {target and base identities plus the stable reviewed-subject identity;
  when this file is in scope, exclude or normalize only the review-record metadata described by
  `security-review`, never the threat model or baseline controls}
- **Coverage:** {each intended file: tool-reviewed, manually reviewed, or excluded with reason;
  link a complete inventory if large. Resolve tool omissions manually; unknown coverage or
  inaccessible required files means incomplete review, not no findings.}
- **Verification limits:** {design/schema checks versus runtime checks; unverified controls.
  Refresh affected review after substantive changes.}
- **Findings:** {finding summary, or None}
- **Resolutions:** {how findings were addressed}
- **Residual risks / owners:** {remaining risk, owner, and follow-up, or None}
- **Related ADRs:** {links, or None}
