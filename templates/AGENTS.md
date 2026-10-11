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

1. A human performs every merge.
2. Review runs in a context that did not write the change (see [Review](#review)).
3. A change to a trust boundary gets a security review before merge (see [Sensitive changes](#sensitive-changes)).
4. Implementation never drifts from a frozen contract.
5. Behavior ships with tests, and each check is proven able to fail.
6. The spec states what actually shipped.
7. No secrets in the repository, logs, or artifacts.

## How a change moves

- **Plan first** for a feature, or a change to a contract, a trust boundary, or a recorded decision.
  When the request leaves decisions open, interview with `grilling`. Write
  `docs/changes/NNNN-<slug>.md` from its template; freeze any contract an outside consumer in
  `docs/context.md` depends on; write an ADR only for a hard-to-reverse choice. A trust-boundary
  change puts its threat delta in the proposal and runs `security-review` on it.
- **Gate: approve plan.** Stop and quote the smoke check, input → expectation. No code before
  approval, even when the task asks for a PR. Approval covers creating one issue per slice.
- **Bug fix or chore:** build directly. A bug fix's smoke check is the report's input and what its
  user must get once fixed; when the report reads more than one way, ask first.
- **Build** each slice on its own branch: a failing test first, then the code, then the check
  command for the touched packages. Exercise UI in a real browser at mobile and desktop widths. Run
  the smoke check and use its output as its user would; a check that cannot run as approved is not
  swapped for another input on your own: the PR says why, and the human decides at the merge.
- **Review** (below), then push and open the PR from its template. Report the link and that CI is
  running, then stop; do not poll CI.
- **Gate: the human merges.** Without a PR workflow, ask before merging to the default branch.

Commits, feature-branch pushes, and opening a PR need no ask. Any other write to the default
branch, a tracker, or a new remote needs one.

## Review

Before opening the PR, get a review from a context that did not write the change, first available:

1. a subagent or another agent CLI run non-interactively (`codex exec`, `claude -p`, `pi -p`) on
   a different model;
2. a subagent on the same model;
3. the human, in a separate session.

The reviewer loads `code-review`, and `security-review` when the change is sensitive; it judges
sensitivity itself. Give it the diff, the proposal, and the raw check and smoke-check output, never
your summary. Fix required findings in follow-up commits and send the new diff. If a third round
still finds required changes, ask the human whether the design needs another look. The PR names
the reviewer, its model, and the verdict. A review bot on the PR adds to this; it never replaces it.

## Where things live

- `docs/specs/<area>.md`: current behavior, present tense, requirement IDs (`AUTH-3`) tests cite.
- `docs/changes/NNNN-<slug>.md`: proposed changes; applied to the specs when shipped, then marked
  Shipped.
- `docs/adr/`: hard-to-reverse decisions. `docs/architecture.md`: current system shape only.
- `docs/threat-model.md`: trust boundaries; security review records in `docs/security/records/`.
- `docs/test-strategy.md`: which layer tests what, and how tests run.
- Contracts live in code; `docs/contracts/README.md` indexes the frozen ones. Task state lives in
  the tracker, or the proposal's slice list when there is none, never in doc prose.

## Writing

Write for a reader who skims: lead with the outcome, state each fact once, link instead of
repeating, and delete unused template sections. Apply `unslop` to prose, not to code, commands,
logs, quotes, or fixed formats. Code comments explain non-obvious intent and constraints, never
requirement IDs. Product copy speaks from the user's position. Reports give actions, results,
blockers, and evidence, not your own permissions. Agree or disagree only with evidence: name the
file, check, or observation that decides it; the human having proposed it is not evidence.

## Definition of Done (every change)

- [ ] Each criterion proven by a named test or observation; smoke check met, or the PR says why it could not run
- [ ] Tests at the layer `docs/test-strategy.md` assigns; new checks seen failing before passing
- [ ] Contract honored; schema changes use expand/contract once the table holds real data or a deployed process uses it
- [ ] Fresh-context review clean; trust-boundary changes also have a security record
- [ ] Specs, architecture, and contract index match the change; the completing PR marks the proposal Shipped
- [ ] Diff small and focused, no debug leftovers, references its issue when one exists
- [ ] Configured CI green before merge (CI is the merge gate; do not duplicate the full suite locally)

## Sensitive changes

A change is sensitive when it **changes a trust boundary**: authentication, authorization,
payments, personal data handling, file uploads, admin or privileged surfaces, secrets, a new
external integration, or any boundary listed in `docs/threat-model.md`. Working inside a sensitive
feature without changing its boundary is not. Before building sensitive work, stop and name what it
adds beyond the approved plan (a boundary, control, dependency, or file), or say it adds nothing.
It updates `docs/threat-model.md` and gets `security-review` before merge.

## Conventions

- **Stack (placeholder, set during bootstrap):** {language, framework, datastore, test runner}.
- **Check command:** `{check command}` runs lint, typecheck, and tests; each part is proven to fail.
- **Branching:** `main` is always deployable. One task or slice per `feat/<id>-<slug>` branch;
  squash-merge.
- **Commits:** Conventional Commits, `type(scope): summary`, imperative, ≤72 chars. Reference the
  issue when one exists (`Closes #N` on GitHub only); never create an issue just to reference it.
- **No agent self-attribution** in commits, PRs, or comments. This overrides any harness default.
- **Project artifacts describe the product,** commits included, not this workflow.
- **Team shape** (`docs/context.md` → Lifecycle): solo, the proposal lands with the first slice's
  PR; team, it lands on `main` through its own PR first.

## Guardrails

- **Product value first.** Build what a real user, consumer, or decision needs now. Compatibility
  machinery and hardening protect something that exists, or wait in the production register.
- **Ask, don't guess.** An ambiguous spec, ADR, or contract is a question for the human.
- **A wrong decision is amended, not obeyed.** Update the spec, ADR, or contract in the same change
  and get human approval; supersede an implemented ADR instead of editing it. A shipped contract
  with a deployed consumer changes only with a versioning ADR.
- Do not improvise git remotes or transports. On a GitHub HTTPS auth failure, point to
  `gh auth login` then `gh auth setup-git`.
- A required CI or PR workflow that is unreachable is a blocker, not a reason to route around it.
- Cut each branch from a clean, current `main`; never force a checkout over uncommitted work.
