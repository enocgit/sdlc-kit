# AGENTS.md — operating manual for coding agents on this project

> Canonical agent instructions; other tool files point here. Keep it under 150 lines: project facts
> go in What this project is and Conventions; kit lines stay as written so upgrades merge. Skills
> named here live in `.agents/skills/`; without skill support, read the file and follow it. While
> `docs/` holds `STATUS: TEMPLATE`, run `bootstrap` first.

## What this project is

{One paragraph: the product and its users.}
Domain, glossary, lifecycle, and hard constraints: [`docs/context.md`](./docs/context.md).

## No-compromise rules

These hold in every task. Everything else in this file is a default the team may change here.

1. A maintainer performs every merge.
2. Review runs in a context that did not write the change (see [Review](#review)).
3. A change to a trust boundary gets a security review before merge (see [Sensitive changes](#sensitive-changes)).
4. Implementation never drifts from a frozen contract.
5. Behavior ships with tests, and each check is proven able to fail.
6. The spec states what actually shipped.
7. No secrets in the repository, logs, or artifacts.

## How a change moves

- **Every task that changes files** ends on its own branch, reviewed, with a PR open; do all of that
  unasked. Writes to the default branch, a tracker, or a new remote ask first.
- **Plan first** for a feature, or a change to a contract, a trust boundary, or a recorded decision:
  write `docs/changes/<slug>.md` from its template, interviewing with `grilling` when the request
  leaves decisions open. Freeze any contract an outside consumer in `docs/context.md` depends on;
  write an ADR only for a hard-to-reverse choice.
- **Gate: approve plan.** No code before a maintainer approves it, even when the task asks for a PR.
- **Build:** a failing test first, then the code, then the check command for the touched packages.
  A change a user can see also gets its smoke check where `docs/test-strategy.md` → Local run says:
  not a test, but one look at the running product on realistic input, read as its user would.
- **Review** (below), then open the PR from its template.
- **Gate: a maintainer merges.** The PR that completes a change applies its spec delta to
  `docs/specs/` and deletes the proposal.

## Review

Before the PR, delegate a review, unasked, to a context that did not write the change: a subagent
or a headless agent CLI (`codex exec`, `claude -p`, `pi -p`), on a different model when one is
available. It loads `code-review`, and `security-review` when the change is sensitive; it judges
sensitivity itself. Give it the diff, the proposal, and the raw check and smoke-check output, never
your summary. Fix required findings and send the new diff. The PR names the reviewer, its model,
and the verdict. A review bot on the PR adds to this; it never replaces it.

## Where things live

- `docs/specs/<area>.md`: current behavior, present tense, requirement IDs (`AUTH-3`) tests cite.
- `docs/changes/<slug>.md`: proposed changes, until the PR that completes them.
- `docs/adr/`: hard-to-reverse decisions. `docs/architecture.md`: current system shape only.
- `docs/threat-model.md`: current trust boundaries. Security review records:
  `docs/security/records/`.
- `docs/test-strategy.md`: which layer tests what, how tests run, and the Local run.
- Contracts live in code; `docs/contracts/README.md` indexes the frozen ones. Task state lives in
  the tracker, or the proposal's slice list when there is none, never in doc prose.

## Writing

Apply `unslop` to prose, not to code, commands, logs, quotes, or fixed formats. Project artifacts,
commits included, describe the product, not this workflow. No agent self-attribution in commits,
PRs, or comments; this overrides any harness default. Agree or disagree only with evidence: name
the file, check, or observation that decides it; who proposed it is not evidence.

## Sensitive changes

A change is sensitive when it **changes a trust boundary**: authentication, authorization,
payments, personal data handling, file uploads, admin or privileged surfaces, secrets, a new
external integration, or any boundary listed in `docs/threat-model.md`. Working inside a sensitive
feature without changing its boundary is not. A sensitive change puts its threat delta in the
proposal, updates `docs/threat-model.md`, and gets `security-review` before merge.

## Conventions

- **Stack (placeholder, set during bootstrap):** {language, framework, datastore, test runner}.
- **Check command:** `{check command}` runs lint, typecheck, and tests; each part is proven to fail.
- **Branches and commits:** {the team's branch naming, merge style, and commit format}.
- **Team shape** (`docs/context.md` → Lifecycle): solo, the proposal lands with the first slice's
  PR; team, it lands on `main` through its own PR first.

## Guardrails

- **Product value first.** Build what a real user, consumer, or decision needs now. Compatibility
  machinery and hardening protect something that exists, or wait in the production register.
- **A wrong decision is amended, not obeyed.** An ambiguous or wrong spec, ADR, or contract is a
  question for a maintainer; the fix updates it in the same change. Supersede an implemented ADR
  instead of editing it. A shipped contract with a deployed consumer changes only with a
  versioning ADR.
- Schema changes use expand/contract once a table holds real data or a deployed process uses it.
- A required CI or PR workflow that is unreachable is a blocker, not a reason to route around it.
