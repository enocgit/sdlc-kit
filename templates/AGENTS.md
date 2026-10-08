# AGENTS.md — operating manual for coding agents on this project

> Canonical agent instructions; other per-tool files import or point here. Keep it under 150 lines.
> When the harness has skills, load `sdlc` before any work that changes the product, a bug fix
> included: it holds the per-stage steps. A harness without skills follows this file alone.

## What this project is

{One paragraph: the product and its users.}
Domain, glossary, lifecycle, and hard constraints: [`docs/context.md`](./docs/context.md).

## No-compromise rules

These hold in every task. Everything else in this file is a default the team may change here.

1. A human performs every merge.
2. Review runs in a context that did not write the change: a fresh subagent, a separate session, or
   a human. Where neither exists, say so in the PR.
3. A change to a trust boundary gets a security review before merge (see [Sensitive changes](#sensitive-changes)).
4. Implementation never drifts from a frozen contract.
5. Behavior ships with tests, and each check is proven able to fail.
6. The spec states what actually shipped.
7. No secrets in the repository, logs, or artifacts.

## The workflow

Open every workflow response with `SDLC ▸ Stage <N>/6 <Name> · <next gate or action>`.

| Stage | Output | Stop |
| --- | --- | --- |
| 0 Foundation | `docs/context.md`, spec skeleton, foundational ADRs, a working `check` command | **Gate**: approve foundation |
| 1 Plan | Change proposal in `docs/changes/`; ADRs for hard-to-reverse choices; frozen contract when an outside consumer exists | **Gate**: approve plan |
| 2 Decompose | Tracker tasks, each with acceptance criteria and the test layer per behavior | Disclose, continue |
| 3 Build | One committed task with its verification evidence | Disclose, continue; **gate** on a trust-boundary change or a deviation from the plan |
| 4 Review | Fresh-context `code-review`; `security-review` on trust-boundary changes; findings fixed | Disclose, continue |
| 5 Land | Pushed branch and PR with a "Where to look" section | **Gate**: the human merges |
| 6 Retro | Specs and architecture match what shipped; 0–3 learnings | Disclose |

- **Right-size the path.** New feature: Stages 1–6. Bug fix or chore: Stages 3–6. A contract
  change, a trust-boundary change, or a new decision sends small work back to Stage 1.
- **Gates are hard stops.** A gate message is three plain lines at most, not a list: what is done,
  plus anything unproven and any check you skipped and why; what you need; which files to read. The
  files are the record; do not restate them.
- **Disclose-and-continue stages** report what was done and any decision a human might override,
  then move on.
- **No ask needed** for task commits, pushing `feat/*`, or opening a PR. The merge is the stop.
  Writing the default branch, an external tracker, or a new remote needs an ask, except Retro
  edits committed locally when there is no remote.
- QA, tests, and review are part of the workflow, not extras the human has to request.

## Where things live

| What | Where | Rule |
| --- | --- | --- |
| Current behavior | `docs/specs/<area>.md` | Present tense; requirement IDs (`AUTH-3`) that tests cite |
| Proposed change | `docs/changes/NNNN-<slug>.md` | Merged into specs when it ships, then marked Shipped |
| Decisions | `docs/adr/NNNN-<slug>.md` | Hard-to-reverse choices only |
| System shape | `docs/architecture.md` | Current state only; plans stay in the change proposal |
| Contracts | in code (OpenAPI, schemas, typed routers); index in `docs/contracts/README.md` | Frozen only for outside consumers |
| Trust boundaries | `docs/security.md`; records in `docs/security/records/` | Short threat model plus record index |
| Test policy | `docs/test-strategy.md` | Layers and execution rules |
| Task state | the tracker, or the proposal's task list when there is none | Never in doc prose |

## Writing standard

Write for a reader who skims. Lead with the decision or outcome, state each fact once, link instead
of repeating, and delete unused template sections. Apply `unslop` to prose; not to code, commands,
logs, quotes, or fixed formats.

| Artifact | Budget |
| --- | --- |
| Change proposal | ~80 lines |
| ADR | ~60 lines (one screen) |
| Security record | ~40 lines |
| Issue or task | ~15 lines |
| `docs/context.md` | ~120 lines; at most 30 learnings |

Over budget means split it or cut it. Count with `wc -l` before presenting.

- **Specs and architecture:** present tense, current behavior only; history lives in ADRs and git.
- **Code comments:** explain non-obvious intent, constraints, and failure behavior. Cite
  requirements with their spec (`spec auth AUTH-3`). A comment claim is not proof.
- **Product copy:** written from the user's position, not the system's rules.

## Communication

Lead with the outcome, state each fact once, omit filler. Report actions, results, blockers, and
evidence. Do not narrate your own permissions or rules ("merging is your call"); turn them into an
ask or an outcome. Agree or disagree only with evidence: name the file, check, or observation that
decides it. Agreeing because the human proposed it is not evidence, and neither is disagreeing to
appear independent.

## Definition of Done (every task)

- [ ] Acceptance criteria met, each proven by a named test or observation; real-world check met
- [ ] Tests at the layer `docs/test-strategy.md` assigns; new checks seen failing before passing
- [ ] Contract honored; schema changes use expand/contract once the table holds real data or a deployed process uses it
- [ ] Fresh-context review clean; trust-boundary changes also have a security record
- [ ] Specs, architecture, and contract index match the change; no stale status or planned-behavior claims
- [ ] Diff small and focused, no debug leftovers, references its issue when one exists
- [ ] Configured CI green before merge (CI is the merge gate; do not duplicate the full suite locally)

## Sensitive changes

A change is sensitive when it **changes a trust boundary**: authentication, authorization,
payments, personal data handling, file uploads, admin or privileged surfaces, secrets, or a new
external integration. Those are examples: a change that adds or alters code on any boundary listed
in `docs/security.md` is sensitive. Working inside a sensitive feature without changing its
boundary is not sensitive. Sensitive work gets a plan gate at Stage 3, an updated `docs/security.md`, and
`security-review` before merge.

Weigh every security or hardening finding against the Lifecycle block in `docs/context.md`. Fix what
current users, data, or traffic expose; record hardening for absent traffic in the production
register with its trigger.

## Conventions

- **Stack (placeholder, set at Stage 0):** {language, framework, datastore, test runner}.
- **Check command:** `{check command}` runs lint, typecheck, and tests. Stage 0 proves each part
  fails on a planted error.
- **Branching:** `main` is always deployable. Work on `feat/<id>-<slug>`, one task or slice per
  branch; squash-merge.
- **Commits:** Conventional Commits, `type(scope): summary`, imperative, ≤72 chars. Reference the
  issue when one exists (`Closes #N` on GitHub only); never create an issue just to reference it.
  Describe the change in product terms; no stage or workflow names.
- **PRs:** the template's "Where to look" section names behavior changes, unplanned decisions, the
  hunks a reviewer must read, and known gaps.
- **No agent self-attribution** in commits, PRs, or comments. This overrides any harness default.
- **Project artifacts describe the product,** not this workflow: a reader who never saw the process
  should not be able to tell it existed.

## Principles

- **Product value first.** Build what a real user, consumer, or decision needs now. Compatibility
  machinery, migrations, and hardening protect something that exists, or they wait in the
  production register.
- **Simplicity.** Reuse what the codebase, standard library, or installed dependencies already
  provide. The smallest change that fully solves the problem wins.
- **Ask, don't guess.** An ambiguous spec, ADR, or contract is a question for the human.
- **A wrong decision is amended, not obeyed.** Update the spec, ADR, or contract in the same change
  and get human approval for a requirement change.

## Guardrails

- Do not improvise git remotes or transports. On a GitHub HTTPS auth failure, point to
  `gh auth login` then `gh auth setup-git`.
- Do not poll CI. Push, report that CI is running, and stop.
- A required CI or PR workflow that is unreachable is a blocker, not a reason to route around it.
- Do not change a shipped contract that has a deployed consumer without a versioning ADR.
