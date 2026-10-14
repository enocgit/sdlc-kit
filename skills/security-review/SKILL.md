---
name: security-review
description: >
  Structured security review of a change that moves a trust boundary: walks the boundary by
  weakness class, traces hostile input to sinks, and writes a short findings-and-resolutions
  record under docs/security/records/. Required before merging a sensitive change; also used on a
  plan that changes a trust boundary.
---

# security-review

Review-only: findings go to the author; this pass does not edit code.

## Before you start

- Read `docs/threat-model.md`: its trust boundaries and controls are the baseline you check against.
- Read the change: the diff against the target branch, including tests, docs, config, and lockfile
  changes; or, for a plan, the change proposal.
- Note the exposure from `docs/context.md` → Lifecycle: who can reach this today, and with what data.

## Walk the boundary

For each entry point the change adds or alters, trace user-controlled input to every sink it
reaches, across files. Check removed or weakened controls as carefully as new code.

| Class | Look for |
| --- | --- |
| Injection | Unparameterized queries, input in shell calls, file paths, templates, or unescaped output |
| Authentication | Missing auth on an endpoint, tokens in URLs or logs, sessions not invalidated |
| Authorization | Missing permission check, object access without ownership check, queries not scoped to user or tenant |
| Data exposure | Secrets or personal data in responses, errors, or logs |
| Configuration | Permissive CORS, debug surfaces, default credentials, missing rate limits on auth or costly endpoints |
| Integrity | Unsigned tokens or webhooks, missing CSRF protection, deserializing untrusted data |
| Cryptography | Weak or homemade algorithms, hardcoded keys |
| Dependencies | Known vulnerabilities, abandoned packages, surprising transitive additions |

Before reporting a finding, confirm the path is reachable and that no framework or upstream control
already blocks it.

## Severity

Rate each finding against current exposure, not worst case:

- **High:** exploitable by someone who can reach the system today. Blocks merge.
- **Medium:** exploitable under a plausible near-term condition. Fix or defer with an owner.
- **Low / hardening:** needs traffic, data, or consumers that do not exist yet. Record it in the
  production register with its trigger; do not expand the diff for it.

## Record

Write `docs/security/records/YYYY-MM-DD-{slug}.md` (today's UTC date from the system clock), at most
~40 lines. Update the trust-boundary table in `docs/threat-model.md` if a boundary moved. A reviewer that cannot write files returns the record, and the
author commits it unchanged.

```markdown
# Security review: {change}

- **Date / subject:** YYYY-MM-DD / {PR, branch, or proposal} at {commit}
- **Reviewed:** {boundaries and files covered}; **not reviewed:** {and why, or "nothing"}

| # | Finding | Severity | Resolution |
| --- | --- | --- | --- |
| 1 | {what and where} | High | Fixed in {commit} |

- **Deferred to register:** {items, or none}
- **Limits:** {what this review could not see, e.g. deployed configuration}
```

An open High finding blocks merge. Required content you could not read is a gap: say so in the
record and block rather than reporting clean.
