# AGENTS.md — Operating manual for AI agents on this project
>
> Canonical agent instructions. `CLAUDE.md`, `.cursorrules`, and similar files should point here.
> **Keep it lean and current** — target ≤200 lines. Single-source: point to the doc/skill, don't
> restate it; every line costs attention and tokens in each session.

## What this project is

<!-- One paragraph: product, users, current phase. Link docs/context.md for depth, including its Lifecycle block. -->
See [`docs/context.md`](./docs/context.md) for domain, glossary, personas, and hard constraints.

## Two altitudes: foundation vs feature

- **Foundation (project-level)** — set once at **Stage 0**: product PRD (`docs/prd/0000-product.md`),
  the few cross-cutting **ADRs** (stack, repo, auth, datastore, API style), architecture skeleton,
  foundational threat model, and core contract. What a first feature can't start without — keep it minimal.
- **Feature-level** (Stages 1–8): brief, PRD, ADRs, and contract slice. Design these as you build.

## How we work: the plan-gated pipeline

The conductor (`sdlc`) routes each stage. Stop at every gate (✅) for explicit human approval.
At non-gate stages, do the work, disclose results and decisions worth overriding, then continue.
Every pipeline response, whichever skill drives it, opens with this one-line status header:
`SDLC ▸ Stage {N}/8 {Name} · {next gate or action}`

| Stage | You produce | Gate |
| ------- | ------------- | ------ |
| 0 — Context + Foundation | filled context and test strategy; product PRD + foundational ADRs + architecture/security skeleton + core contract | ✅ bootstrap: context filled, then approve foundation; ✅ adopt: approve reconstructed foundation |
| 1 — Spec | _(optional)_ brief `docs/briefs/NNNN-*` for a fuzzy idea → hardened PRD in `docs/prd/` (no issues yet) | ✅ approve PRD |
| 2 — Architecture + Contract | ADR(s), updated `docs/architecture.md`, `docs/security.md` (sensitive areas), **frozen** contract artifact | ✅ approve approach + freeze |
| 3 — Decompose | tracker issues (GitHub by default; the tracker is the record) | disclose breakdown |
| 4 — Implement | code on a `feat/*` branch, one task at a time | ✅ approve compact in-session plan per task |
| 5 — QA | proportional local verification + runtime observation or a relevant non-runtime check; CI green now or after PR creation | — |
| 6 — Review | clean diff, findings fixed (`security-review` if sensitive) | inline — no gate |
| 7 — Land | PR opened where hosting supports it. Without PR support, push the branch if a remote exists, run any available CI, and the human merges it directly; with no remote, the human merges the local branch. **GitHub:** carries `Closes #N`, issue closes on merge. **Any other tracker / local-only:** no keyword — task → _In review_, completed after the merge (see `sdlc` skill) | ✅ human merges |
| 8 — Retro | 0–3 durable learnings curated per task; after the final child, feature artifacts reconciled and parent epic completed | — |

> Establish Stage 0 once; features then run Stages 1→8. Bug fixes run Implement → QA → Review → Land → Retro;
> chores run Implement → Review → Land → Retro. Contract changes, sensitive areas, and decisions
> require the full feature path.

## Where things live

- **Product PRD** (project-level vision/scope, set at Stage 0) → `docs/prd/0000-product.md`
- **Feature PRDs** → `docs/prd/NNNN-{slug}.md` (numbered from 0001, status-tracked)
- **ADRs** (decision history; superseded, never rewritten) → `docs/adr/NNNN-{slug}.md` — _foundational_ ADRs
  (stack/repo/auth/datastore/API) are set at Stage 0; _feature_ ADRs are added per feature
- **Architecture** (current system shape, living) → `docs/architecture.md`
- **Contracts** (the integration source of truth) → in the codebase (`api/openapi.yaml`,
  tRPC routers, `schema.prisma`, Zod schemas). See `docs/contracts/README.md`.
- **Task status** → your tracker (GitHub Issues/Projects), the single source of truth, reported live
  by `project-status`. _Local-only (no external tracker):_ `docs/progress.md` **is** the tracker
- **Test strategy, verification policy, and Definition of Ready/Done** → `docs/test-strategy.md` and this `AGENTS.md`

## Documentation writing standard

Write docs, issues, and PRs for contributor decisions and verification, not narrative.
Lead with status, scope, outcome, rationale, constraints, and open questions; link authoritative details rather than duplicate facts.
Each bullet, numbered item, checkbox, or table cell should express one clear rule, decision, or outcome.
Prefer one sentence per point, use a second only to explain or qualify it, and split additional obligations into separate points rather than hiding them in semicolons or inline lists.
Write current-state docs in the present tense: no "used to", "no longer", or migration narration; history belongs in `docs/adr/` and git.
Each checkbox should have one independently verifiable outcome. Preserve requirement IDs when splitting their supporting rules.
Keep existing document structure and PRD/ADR introductory paragraphs; impose no point-count, word, or line quotas.
Preserve exact limits, exceptions, risks, security boundaries, failure behavior, compatibility, verification limits, and fixed formats.
Remove unused scaffold and filler; name owners/triggers for deferred sections. Use complete, plain English, not compressed fragments.
Keep process instructions here and prompts in templates. Use underscores for emphasis and asterisks for bold; apply `unslop` with its canonical scope and exclusions.

**Briefs and PRDs:** State each requirement once, with only the detail needed for approval and verification.
Briefs explain the problem; PRDs describe observable behavior and testable rules. Define technical terms on first use.
Link implementation decisions to ADRs/contracts and preserve exact limits, exceptions, and privacy.

**Code comments:** Explain non-obvious intent, constraints, state transitions, and failure behavior beside relevant code.
Keep comments precise and durable; avoid syntax narration and quotas. Link essential reasons and workaround removal conditions.
Put change summaries and verification results in the PR; check comment claims against implementation, not as proof.

## Communication standard

Keep user-facing replies compact: lead with the outcome, state each fact once, and omit filler.
Follow standing workflow rules silently in ordinary prose: do not append compliance summaries, repeat routine permissions,
guardrails, or planned mechanics, or narrate the process or rule behind an action ("per the gate protocol").
The mandatory status header, gate/approval prompts, and safety, progress, blocker, or decision messages remain required. Report actual actions, results, blockers, deviations, and decisions needed; mention a guardrail only when it changes available action.
Use complete sentences for gates, security warnings, irreversible actions, ordered steps, and complex trade-offs. Expand when asked; runtime safety and progress rules win.

## Definition of Ready (before a task enters Implement)

- [ ] Acceptance criteria are written and testable
- [ ] Applicable contract frozen; fast-path N/A recorded when no integration contract applies
- [ ] Frozen contract matches its accepted ADR and the `docs/architecture.md` update
- [ ] No open questions remain (resolved during stress-test, at the Spec gate)
- [ ] Task is small enough to ship in ~a day (else split it)

## Definition of Done (every task)

- [ ] Meets the acceptance criteria in its PRD/issue
- [ ] Honors frozen contracts; fast-path N/A recorded when no integration contract applies
- [ ] DB schema changes follow expand/contract (migrate → deploy → clean up) **once the table holds
      real data or any deployed process reads or writes it** — before that, change it outright
- [ ] Verification evidence matches the risk (see `docs/test-strategy.md`). Name the smallest
      concrete local check that proves the change: docs/prose → links or rendering; styling, static
      markup, attributes, or copy → targeted render/browser or manual visual inspection;
      configuration/generated output → syntax, schema, or generation; runtime behavior → focused
      tests and runtime observation. Broaden local checks to all impacted packages/modules for
      shared paths, contracts, or security-sensitive areas; reserve the full suite for broad or
      high-risk dependency fan-out or an explicit project rule.
- [ ] **Configured CI is green before merge** (lint, typecheck, test, build, and any other
      configured or policy-required checks); this is a remote merge gate, not a reason to duplicate
      the full suite locally. If CI runs after PR creation, finish proportional local QA and review
      before opening it. N/A _only_ where no CI workflow exists; unreachable required CI blocks.
- [ ] `code-review` + `simplify` clean; a [sensitive area](#sensitive-areas) also needs
      `security-review` with complete scoped coverage per `sdlc`, recorded in `docs/security.md`
- [ ] Diff hygiene: small and focused, references the issue, no stray/debug code
- [ ] Current-behavior claims stay accurate per task; distinguish approved from implemented behavior
      per `sdlc`. After the final child, reconcile all feature artifacts with implementation evidence
- [ ] Tracker linked and current (rules by tracker/hosting: see the Stage 7 row above) — closure
      itself is a post-merge step, not required before Land

## Conventions

- **Stack (placeholder — set at Stage 0):** TypeScript + React (frontend), Node (backend) are illustrative defaults; replace with your real stack when you fill `docs/context.md`.
- **Branching — GitHub Flow:** `main` is always deployable. Work on short-lived `feat/{id}-{slug}` branches → PR → merge → deploy. Environments are deploy targets driven by CI, not long-lived branches. One feature per branch; use a git worktree only as an explicit manual escape hatch when requested. The operator supplies a private, new or empty path outside every checkout and runs `feature-start`'s generic Git-only recipe.
- **Where planning commits land.** Land each planning package on **`main`**, never a feature branch:
  the Stage 0 context + foundation package at the foundation gate (adoption: the combined Stage 0
  gate), then the Stage 1 PRD + Stage 2 ADRs, architecture/security updates, and frozen contract
  once after Stage 2, with a threat model in `docs/security.md` and `security-review` on the diff
  when a sensitive area is touched. Stage 4 cuts `feat/{id}-{slug}` from a ref that must already
  hold the frozen contract, so ask for the landing action by remote state: **no remote** → commit
  locally; **remote, unprotected `main`** → commit and push; **protected `main`** →
  `plan/{NNNN}-{slug}` → PR → merge, then branch `feat/*`. The branch carries the task
  implementation plus its required task-scoped tests and docs, and a frozen contract changes only
  via a new ADR. Per-task learnings land before the next task, and final-child reconciliation lands
  **before completing the parent epic**; an empty Retro needs no landing action.
- **Commits — Conventional Commits.** `type(scope): summary` — imperative, ≤72 chars. Types:
  `feat` `fix` `refactor` `test` `docs` `chore` `perf` `build` `ci`. Reference the issue
  (`Refs #123` / `Closes #123` — GitHub only; elsewhere its key). Small logical commits, not a blob.
- **PRs:** small and reviewable; one feature per branch; reference the issue; fill the PR template
  (contract, security impact, and verification). Squash-merge to keep `main` linear.
- **No agent self-attribution.** Commits/PRs describe the _change_, not the tool that made it — no
  "Made with {agent}", "Generated by …", or `Co-Authored-By:` trailer naming an AI, in commits, PR
  titles/bodies, or code comments. Authorship is the human's; this overrides any runtime default.
- **Contract-first:** define and freeze the interface before FE/BE implement in parallel.
- **Project-facing artifacts cite durable docs, not process mechanics.** Reference the durable artifact — "the frozen contract
  (contract 0001, ADR-0004)" — and stop; a reader who never saw this process must not be able to tell it existed. Kit-owned operating documentation and templates may describe the process they govern.
- **Ask, don't guess:** if a PRD/ADR is ambiguous, stop and ask rather than assume.
- **A wrong decision is amended, not obeyed.** When implementation disproves a recorded decision, supersede it in the same change as the code and name the assumption that failed. A silently divergent implementation is worse than either choice; a _shipped_ contract still needs the versioning decision below.

## Principles

- **Simplicity first.** Prefer the smallest direct solution that fully solves the problem; add an
  abstraction only when a real, present need justifies it — not future speculation.
- **Reuse before building.** Prefer existing, well-maintained libraries over bespoke code when they fit; if unsure, research and weigh the options (fit, maintenance, footprint) first.
- **Pay only for what exists.** Compatibility machinery, history narration, and tests for unobserved
  failures protect a real consumer, real data, or an observed incident, not a hypothetical one. Read
  the Lifecycle block in `docs/context.md` before building any of them; while it shows nothing
  deployed, no real data, and no traffic, change the shape outright, keep current-state docs in the
  present tense, and record each deferral in the production register instead. If you don't know
  whether something outside this change depends on it, ask; don't assume either way.

## Sensitive areas

**Canonical list** (other docs and skills point here): **authentication, authorization, payments,
PII/KYC, file uploads, and admin/privileged surfaces.** A change touching these updates
`docs/security.md` during foundation or Architecture as applicable and gets `security-review` before each planning or implementation merge.

## Vendored skill overrides

Third-party snapshots supply techniques; this file and the `sdlc` conductor own paths, transitions,
and safety. Run stage-bound snapshots only when `sdlc` routes to them, and apply these overrides:

- Before using the `brainstorming` visual companion, set `SUPERPOWERS_DISABLE_TELEMETRY=1` to block
  its branding request. Keep it on loopback with an SSH tunnel, never plaintext non-loopback mode;
  use its default temporary session directory and do not pass `--project-dir`. Ignore its instruction to commit or write under `docs/superpowers/`; the conductor owns the artifact and gate.
- For `improve-codebase-architecture`, treat `CONTEXT.md` as `docs/context.md`; do not invoke its
  unavailable `codebase-design` or `domain-modeling` dependencies, and skip its CDN-backed report.
- For an opt-in worktree, use the generic Git-only `git worktree add` and non-forced
  `git worktree remove` commands in `feature-start`; the operator owns platform-specific path
  selection, privacy, and containment checks.
- Do not use `webapp-testing`'s bundled `with_server.py`; use the project's lifecycle runner or an
  already-running server. Wait for an app-specific readiness signal, not mandatory `networkidle`.

## Guardrails

> These rules depend on agent adherence, CI, and review gates; this file alone enforces nothing.

- Do not commit, push, open PRs, or **merge** unless asked — **merge is always the human's call.**
- **At Land, don't poll CI.** With a PR workflow, open the PR and report CI running. With CI but no
  PR workflow, push the branch to start CI and report the run. Then stop at the human merge gate —
  don't `gh run watch` or keep the turn polling. Required CI must be green before the human merges.
- Don't improvise git transports or remote URLs. If a GitHub HTTPS push fails on auth, surface it
  and point to `gh auth login` followed by `gh auth setup-git`. Change a remote URL only after the
  human approves the reviewed URL, using `git remote set-url origin {url}`; never silently switch
  transports or push through an ad-hoc URL.
- Do not change a _shipped_ contract without a versioning/deprecation decision (new ADR).
- Do not write a breaking DB migration against a table holding real data or read/written by any
  deployed process — use expand/contract so `main` stays deployable through the rollout.
- A change touching a [sensitive area](#sensitive-areas) gets a threat model + `security-review`.

## Outcome summaries

For tasks needing manual verification (UI, flows, integrations), end with a short **QA checklist**
of steps and expected results; skip it when fully tested.
