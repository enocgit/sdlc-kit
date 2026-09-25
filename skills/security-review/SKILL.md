---
name: security-review
description: >
  Performs a structured security review of the complete target-to-tree diff: walks the changed
  trust boundaries and attack surface by OWASP weakness class, traces data flows, verifies that
  intended file scope matches actual coverage, and records findings, exclusions, and resolutions in
  a dated file under docs/security/records/ with a matching index entry in docs/security.md. Mandatory
  before landing any sensitive-area change; use at Stage 0/0b/2 for
  sensitive planning packages and at Stage 6 for the implementation diff.
---

# security-review

A maintained adaptation of the OWASP Secure Agent Playbook "Play: Security Code Review",
re-scoped from full-codebase audit to the diff this pipeline reviews before landing. Attribution
and license live in `NOTICE.md` and `LICENSE.txt`.

This pass is review-only. It never edits code. Findings route to the author; resolutions are
recorded, not applied silently.

## Scope and coverage

Review the complete target-to-tree delta on a clean materialization: changed lines with enough
context to judge them, plus every file the change adds, removes, or retypes.

Reconcile intended file scope with actual coverage before starting: list the files the change
should touch per the task, plan, or contract, then compare against the diff. The reviewed scope
must include docs, tests, and new files affected by the change. Any inaccessible required file
blocks readiness rather than being skipped. Record reviewed identity, exclusions, and limits in the
dated review record, and index it in `docs/security.md` — an exclusion needs a stated rationale, not
silence.

Establish context first. For every applicable sensitive-area review (Stage 0/0b/2/6), read the
adopter project's current `docs/security.md` before analyzing the changed files. Treat that threat
model as the required baseline: apply its project-specific threats, trust boundaries, mitigations,
data-sensitivity rules, and domain-specific business-logic and abuse controls to the diff. Do not
substitute generic OWASP coverage for a project control. A missing, templated, stale, or inaccessible
baseline blocks readiness and must be reported as a coverage gap.

- **Trust boundary**: server-side, client-side, library, CLI, infrastructure?
- **Data sensitivity**: credentials, PII, financial or health data?
- **Exposure**: internet-facing, internal, or local-only?
- **Language/framework**: determines which vulnerability classes apply.

## Review by weakness class

Walk the classes in priority order — highest impact first. For each, look for the signals the
changed code introduces or weakens.

**Injection (CWE-74, OWASP A03):** string concatenation in queries, unparameterized SQL, raw ORM
queries; user input in exec/spawn/system calls; unescaped output rendering, unsafe DOM writes,
server-side template evaluation; user input in file paths without canonicalization; CRLF or log
injection.

**Authentication and session (CWE-287, OWASP A07):** hardcoded credentials or API keys; endpoints
missing authentication; session tokens in URLs or logs; missing session invalidation on logout or
password change; JWT issues — `none` algorithm, missing expiry, weak signing key; missing MFA on
sensitive operations.

**Authorization (CWE-862, OWASP A01):** missing authorization checks on new endpoints or
functions; object references without ownership validation (IDOR); horizontal or vertical privilege
escalation; queries that don't filter by user or tenant.

**Cryptography (CWE-327, OWASP A02):** MD5/SHA-1/DES/RC4 for security purposes; ECB mode;
hardcoded keys or IVs; custom crypto implementations; RSA below 2048 bits or AES below 128;
missing encryption at rest or TLS enforcement.

**Data exposure (CWE-200, OWASP A01):** sensitive data in errors, stack traces, logs, or API
responses beyond what the consumer needs; credentials in source, configs, or URLs; debug mode in
production configuration.

**Security misconfiguration (OWASP A05):** default credentials; debug endpoints or admin panels
enabled; permissive CORS; directory listing; missing rate limiting on sensitive endpoints.

**Deserialization and integrity (CWE-502, OWASP A08):** deserializing untrusted data; unsigned
cookies or tokens; missing CSRF protection on state-changing operations; unvalidated data from
untrusted sources crossing a trust boundary.

## Diff-specific analysis

A diff review differs from a full audit. For the changed delta:

- Focus on changed lines and their immediate context; do not re-audit unchanged code beyond what
  the change interacts with.
- Verify that security controls in surrounding (unchanged) code are preserved — look for removed
  validation, deleted auth checks, or weakened sanitization as deliberately as for added flaws.
- Verify that new endpoints or entry points carry authentication and authorization matching the
  existing patterns.
- Trace user-controlled input from new entry points (parameters, headers, bodies, uploads) to sinks
  (queries, exec calls, output, file writes) across files, including between the changed code and
  the modules it calls.
- Treat new dependencies as part of the attack surface: known CVEs, deprecated or abandoned
  packages, unexpected transitive additions in the lockfile diff.

## Findings

For each issue record: location (file and line or symbol), the vulnerable code, a concrete attack
scenario, a proposed fix, and confidence — HIGH for a confirmed path, MEDIUM if contextual, LOW if
heuristic. Re-verify each finding before reporting: confirm the path is reachable and that no
framework, middleware, or upstream control already neutralizes it; discard what isn't genuine.
State positive observations too — the controls that are present and correct.

## Record the review in docs/security/records/

For sensitive-area changes, the review is not complete until a dated record is written under
`docs/security/records/` and its current entry is indexed in `docs/security.md`. Use one file per
feature or an append-only log; never edit a prior record. The record uses a stable review-subject
identity captured from the clean materialization before the record is updated:

- Reviewed identity: target and base identities plus the reviewed subject identity (tree or content
  identity) for the materialized files.
- If `docs/security.md` is part of the reviewed subject, exclude or normalize only these review-record
  metadata fields when computing the subject identity: scope/date, reviewed identity, coverage,
  verification limits, findings, resolutions, residual risks/owners, and related ADRs. Threat-model,
  baseline-control, and other substantive security content remains in the subject identity.
- Record-only updates to those metadata fields do not invalidate the subject review. Any substantive
  security baseline, threat-model, control, or scope change requires a fresh subject identity and a
  rerun of this review.
- Scope: files reviewed; exclusions with rationale; coverage gaps, if any, and why they are
  acceptable or blocking.
- Findings with severity and confidence; resolutions — fixed, mitigated, accepted with rationale,
  or deferred to a tracked item.
- Limits: what this review could not see (runtime behavior, deployed configuration, load
  conditions).

An unresolved Critical or HIGH finding blocks landing. Inaccessible required files block readiness.

## Verification of the review

- [ ] Intended scope reconciled with actual diff coverage, including docs, tests, and new files
- [ ] The current project `docs/security.md` baseline was read and its project-specific threats,
  mitigations, business-logic controls, and abuse controls were applied
- [ ] All applicable weakness classes walked against the changed code
- [ ] Removed or weakened controls checked as deliberately as added flaws
- [ ] Each finding re-verified and confidence-rated
- [ ] A dated record under `docs/security/records/` contains identity, scope, exclusions, findings,
      resolutions, and limits; `docs/security.md` indexes the current record
