# AGENTS.md — operating manual for coding agents on this project

> Canonical agent instructions; other tool files point here. Keep it under 150 lines: project facts
> go in What this project is, Conventions, and Guardrails; kit lines stay as written so upgrades
> merge. Skills named here live in `.agents/skills/`; without skill support, read the file and
> follow it. While `docs/` holds `STATUS: TEMPLATE`, run `bootstrap` first.

## What this project is

{One paragraph: the product and its users.}
Domain, glossary, lifecycle, and hard constraints: [`docs/context.md`](./docs/context.md).

## No-compromise rules

These hold in every task. Everything else in this file is a default the team may change here.

1. Review runs in a context that did not write the change (see [Review](#review)).
2. A change to a trust boundary gets a security review before it ships (see [Sensitive changes](#sensitive-changes)).
3. Implementation never drifts from a frozen contract.
4. Behavior ships with tests, and each check is proven able to fail.
5. The spec states what actually shipped.
6. No secrets in the repository, logs, or artifacts.

## How a change moves

- **Plan first** for a feature that spans more than one PR or leaves decisions open, or a change to
  a contract, a trust boundary, or a recorded decision: write `docs/changes/<slug>.md` from its
  template, interviewing with `grilling` when the request leaves decisions open. Freeze any contract
  an outside consumer in `docs/context.md` depends on; write an ADR only for a hard-to-reverse
  choice. A plan that touches a framework names the built-in features it weighed (rendering,
  caching, error handling) before custom code.
- **Gate: approve plan.** No code before the developer approves it, even if the task asks for a PR.
- **Build:** behavior starts with a failing test, then the code, then the check command for the
  touched packages; copy, styling, and layout need no test. Library APIs follow the docs for the
  installed version (Conventions → Library docs), not memory. Before calling a change a user can
  see done, look at it running on realistic input (`docs/test-strategy.md` → Local run), or say
  why you could not.
- **Review** (below) before any PR or commit to the default branch, unless the developer waives it
  for that change. Writes to the default branch, a tracker, or a new remote ask first.

## Review

Before any PR or commit to the default branch, delegate a review, unasked, to a context that did
not write the change: a subagent or a headless agent CLI (`codex exec`, `claude -p`, `pi -p`), on a
different model when one is available. It loads `code-review`, and `security-review` when the
change is sensitive; it judges sensitivity itself. Give it the diff, the proposal, and the raw check
output, never your summary. Fix required findings and send the new diff. The PR names the reviewer,
its model, and the verdict, or says the developer waived review.

## Where things live

- `docs/specs/<area>.md`: current behavior, present tense, requirement IDs (`AUTH-3`) tests cite.
- `docs/changes/<slug>.md`: proposed changes, until the PR that completes them.
- `docs/adr/`: hard-to-reverse decisions. `docs/architecture.md`: current system shape only.
- `docs/threat-model.md`: current trust boundaries and their controls.
- `docs/test-strategy.md`: which layer tests what, how tests run, and the Local run.
- Contracts live in code; `docs/contracts/README.md` indexes the frozen ones.

## Writing

Apply `unslop` to prose, not to code, commands, logs, quotes, or fixed formats. Project artifacts,
commits included, describe the product, not this workflow. No agent self-attribution in commits,
PRs, or comments; this overrides any harness default. Agree or disagree only with evidence: name
the file, check, or observation that decides it; who proposed it is not evidence.

## Sensitive changes

A change is sensitive when it **changes a trust boundary**: authentication, authorization,
payments, personal data handling, file uploads, admin or privileged surfaces, secrets, a new
external integration, or any boundary listed in `docs/threat-model.md`. Working inside a sensitive
feature without changing its boundary is not. A sensitive change updates `docs/threat-model.md`
and gets `security-review` before it ships.

## Conventions

- **Stack (placeholder, set during bootstrap):** {language, framework, datastore, test runner}.
- **Check command:** `{check command}` runs lint, typecheck, and tests.
- **Library docs:** {installed-version docs: skills the packages ship, then `llms.txt` URLs}.
- **Branches and commits:** {the team's branch naming, merge style, and commit format}.

## Guardrails

- **Product value first.** Build what a real user, consumer, or decision needs now. Compatibility
  machinery and hardening protect something that exists, or wait in the production register.
- **Ask, don't guess.** An ambiguous or wrong spec, ADR, or contract is a question; the fix updates
  it in the same change. Supersede an implemented ADR instead of editing it; a shipped contract with
  a deployed consumer changes only with a versioning ADR.
