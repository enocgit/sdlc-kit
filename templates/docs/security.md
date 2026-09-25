# Security & threat model

> Lightweight, living security doc. Update it at Foundation or Architecture whenever a
> **sensitive area** listed in `AGENTS.md` or a trust boundary changes, then revisit it at review.
> This is a working threat model, not a formal security audit.
>
> **Layout:** this file holds current truth — per-feature threat models, baseline controls, and the
> records index. Dated review records live in `docs/security/records/` (one file per feature, or an
> append-only log). A record is never edited after it is written; a new record supersedes it, and
> this file's index always points at the current one.

## Writing rules

- A feature's threat model is design content, not status: record planned and enforced controls
  without marking implementation progress — the tracker and ADRs own that state.
- Reference the shared actors and trust boundaries from the foundation threat model; restate only
  what the feature changes or adds.
- Keep each feature section scannable — header `### Feature NNNN — {name} (PRD NNNN, ADR-NNNN)`,
  the actors/boundaries this feature adds, then the threat table.

## Threat model (per sensitive feature)

For each feature, separate planned controls from currently enforced controls, and link verification
evidence for each enforced control. Approval or schema tests alone do not establish runtime
enforcement; update a control when its state changes, not on a schedule.

For each feature, record:

- actors, including malicious actors — as a delta on the foundation set;
- sensitive data;
- trust boundaries;
- behavior when an input is hostile; and
- behavior when a dependency or webhook returns false information.

### Feature NNNN — {name} (PRD NNNN, ADR-NNNN)

<!-- Actors and trust boundaries this feature adds. Threat table below. -->

| Asset / data | Threat | Mitigation | Owner |
| ------------ | ------ | ---------- | ----- |
| {asset} | {threat} | {control, linked to its verification evidence when enforced} | {who} |

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

## Review records

`security-review` is mandatory for authentication, authorization, payments, PII/KYC, file uploads,
and admin/privileged surfaces (canonical list in `AGENTS.md`). A sensitive change is reviewed twice:
on the planning package before it lands on `main`, and on the implementation change before merge.
Close its findings before merge, and record decisions that change the security posture in an ADR.

### Records index

| Date | Feature | Review | Findings | Residual risk | Record |
| ---- | ------- | ------ | -------- | ------------- | ------ |
| YYYY-MM-DD | {feature} | planning / implementation | {count and severity, or None} | {one line} | `records/{file}.md` |

Each record binds the target and base identities to a stable reviewed-subject identity. When
`docs/security.md` is in scope, exclude or normalize only review-record metadata when computing that
identity; keep the threat model and baseline controls in scope. Record-only updates do not
invalidate the review. A substantive threat-model, baseline-control, or scope change needs a fresh
identity and review.

Every record uses the field order below, so any record scans the same way:

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
