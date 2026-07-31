---
name: sdlc
description: >
  Orchestrates an end-to-end, plan-gated software build pipeline: routes each stage to the right
  skill while enforcing human approval gates. Covers discovery, PRD, stress-test, architecture,
  API contracts, decomposition, implementation, QA, review, landing, and retro. The single entry
  point for the workflow. Use when the user wants to build a feature or product the disciplined
  way, start or resume structured development, asks "what stage are we at" / "what's next", or
  says "start the sdlc" / "run the pipeline".
---

# sdlc — the conductor

You are running a fixed, plan-gated pipeline. Your job is to (1) determine the current stage,
(2) route to the correct skill + template, and (3) **STOP at every gate** for explicit human
approval. You guide; you do not silently skip ahead.

## Two altitudes (read this first)

Artifacts live at two altitudes — keep them straight:

- **Project-level (foundation)** — set once, early (Stage 0): the **product PRD**
  (`docs/prd/0000-product.md`), the few cross-cutting **ADRs** (stack, repo layout, auth,
  datastore, API style), the **architecture skeleton**, and the **core contract**. These belong
  to no single feature.
- **Feature-level** — produced per feature (Stages 1–8): a brief, a feature PRD, feature ADR(s),
  and a contract _slice_.

Don't design every feature up front — but DO lock the handful of foundational decisions a first
feature can't start without. Let everything else emerge per-feature.

## First: orient

**Resolve skills from the skill dirs.** Look for this pipeline's skills in the user-global
dirs (`~/.agents/skills`, `~/.claude/skills`) **and** the project's local skills dir — not the
project alone. A skill may be installed globally; don't assume a stage's skill is missing just
because it isn't vendored in the repo. If it's in neither place, resolve in this order: (1) use the
named skill if present; (2) else use your **runtime's equivalent** — several stage skills are named
after Claude Code's commands (`code-review`, `simplify`, `verify`, `run`, `security-review`) and other
runtimes have their own (e.g. Codex `review` ≈ `code-review`), so use that; (3) only if there's no
skill **and** no runtime equivalent, use the manual `fallback` in `required-skills.yml`.

1. Read `AGENTS.md` and `docs/context.md`. **Stage 0 is incomplete** if either is missing OR
   still contains template markers — an unfilled `docs/context.md` carries a `> STATUS: TEMPLATE`
   line and/or `{placeholder}` tokens. The installer ships these files pre-created, so do NOT
   rely on existence alone: check the context is actually filled. If Stage 0 is incomplete, run
   the on-ramp and treat **"context filled" as a gate** — do not advance to Discovery until the
   STATUS marker is gone and the sections are completed for this project:
   - **`bootstrap` (new project, little/no code):** two parts —
     - **0a Context:** the kit's installer already scaffolded `docs/`, `AGENTS.md`, and the
       one-line `CLAUDE.md` pointer — if any are missing, re-run the kit's `install.sh` (it's
       non-destructive) rather than recreating them by hand. Then interactively fill
       `docs/context.md`. Do NOT run `init` — there's no codebase yet. _Gate: context filled._
     - **0b Foundation:** produce the **project-level** artifacts — a product PRD at
       `docs/prd/0000-product.md`, the few unavoidable cross-cutting ADRs (stack, repo layout,
       auth, datastore, API style), the `architecture.md` skeleton, and a core contract scaffold.
       Keep it minimal: only decisions a first feature genuinely can't start without — let the
       rest emerge per-feature. **GATE: approve the foundation before Discovery.**
   - **`adopt` (existing codebase):** run `improve-codebase-architecture` (and `init`) to
     reverse-engineer `context.md` + `architecture.md` and **backfill the foundational ADRs**
     (stack, repo, auth, datastore already baked into the code). That reverse-engineered set IS
     the project-level foundation. Note known **tech-debt / risky areas** in `architecture.md`
     (and file actionable ones as issues); the first feature to validate the workflow is simply
     your first Stage 1 Spec. **GATE: approve.**
   - **If these files already exist** (`AGENTS.md`/`CLAUDE.md`/`docs/`), do NOT overwrite. Merge:
     back up or section-merge, preserve the team's content, surface conflicts. Never clobber.
2. **Right-size the path.** Classify the change before routing:
   - **Feature / user-facing / risky** → full pipeline (0→8).
   - **Bug fix / small enhancement** → skip to **4 Implement → 5 QA → 6 Review** (reference an
     issue; no PRD/contract/ADR).
   - **Chore / docs / dep bump** → **4 → 6**, trivial diff, CI green.
   - The moment a "small" change touches a **contract**, a **security-sensitive area**, or makes
     a **decision**, it graduates to the full path. When unsure, ask.
3. Read the tracker (via `gh` / `project-status`) and the active PRD to infer the current stage and
   feature (local-only mode: read `docs/progress.md`).
4. State the chosen path, current stage, and next action to the user before proceeding.

## Status header (every response)

Open every substantive response with one compact line, so the user — and you — always know where
the pipeline is:

`SDLC ▸ Stage {N}/8 {Name} · {next gate or action}`

Examples (on-ramp sub-stages keep their letter — `0a`/`0b`/`0adopt`):
- `SDLC ▸ Stage 0b/8 Foundation · next gate: approve foundation`
- `SDLC ▸ Stage 1/8 Spec · next gate: approve PRD`
- `SDLC ▸ Stage 4/8 Implement · task #5 · next: plan approval`
- `SDLC ▸ Stage 6/8 Review · running security-review (sensitive area)`

One line only; skip it only for trivial acknowledgements. It doubles as your own anchor — restating
the stage each turn is what keeps you from drifting off-process over a long conversation.

## Borrow the technique, not the workflow

The community skills below are **techniques**, not the pipeline. Each was authored standalone and
carries its own opinions about _where it writes_ and _what it does next_ — those opinions are wrong
here, because **this conductor owns the workflow.** When you run a borrowed skill, use its method
and **override its workflow**:

- `brainstorming` → use its discovery method (explore → **one question at a time** → approaches →
  design), but land the artifact as the **(optional) Stage-1 brief** at `docs/briefs/NNNN-{slug}.md`
  and STOP. Reach for brainstorming + a brief only when the idea is fuzzy; a well-understood feature
  skips both and goes straight to `to-prd`.
  Discovery is exploratory — **no code.** Do **not** write to `docs/superpowers/specs/`, and do
  **not** auto-run `writing-plans`; the next step is the Stage 1 Spec (`to-prd`), then the gate.
- `documentation-and-adrs` → ADRs go to **`docs/adr/NNNN-{slug}.md`** (this project's convention),
  never `docs/decisions/`.
- `writing-plans` → use its decomposition method at Stage 3, but write the result to the tracker.
  Do **not** create `docs/superpowers/plans/`; the tracker is the record.
- Any skill that wants to open tracker issues/epics → **defer to Stage 3 Decompose.** The Spec stage
  produces a PRD, not issues.

If a borrowed skill's default fights an `AGENTS.md` convention, **`AGENTS.md` wins.**

## Documentation writing standard

Follow the documentation writing standard in `AGENTS.md`; it is the single source. Apply it to every
durable artifact this conductor creates or updates, and trim borrowed-skill output to match before
each gate.

## The stages, skills, and gates

| Stage | Use skill | Output | After producing output |
|-------|-----------|--------|------------------------|
| 0a Context (new) | installer-scaffolded templates (fill) | `AGENTS.md`, filled `docs/context.md` | gate: context filled |
| 0b Foundation (new) | `documentation-and-adrs` | `docs/prd/0000-product.md`, foundational ADRs (→ `docs/adr/`), `architecture.md` skeleton, core contract scaffold (**trim `docs/contracts/README.md`** to real/`(future)` paths — never leave template examples) | **GATE — approve foundation** |
| 0 adopt (existing) | `improve-codebase-architecture` + `init` | reverse-engineered context/architecture + backfilled foundational ADRs (**point `docs/contracts/README.md` at the existing contract source**; note tech-debt/risks in `architecture.md`) | **GATE — approve** |
| 1 Spec | `brainstorming` (method only) → `to-prd` → `grilling` | **optional** Stage-1 brief `docs/briefs/NNNN-*.md` (only for a fuzzy/speculative idea — else skip straight to the PRD), then hardened PRD `docs/prd/NNNN-*.md` (no issues yet) | **GATE — approve PRD** |
| 2 Architecture + Contract | `documentation-and-adrs` | ADR(s) in `docs/adr/`, updated `docs/architecture.md`, `docs/security.md` (sensitive areas), **frozen** contract artifact in repo (OpenAPI/tRPC/schema) | **GATE — approve approach + freeze interface** |
| 3 Decompose | `writing-plans` + `project-status` | **tracker issues** (GitHub by default) shaped per `.github/ISSUE_TEMPLATE/{epic,task}.md` (the tracker is the record — no in-repo mirror; other trackers: their native issue types; local-only: feature + task rows in `docs/progress.md`) | disclose the breakdown, then continue |
| 4 Implement | `feature-start` (branch; `using-git-worktrees` only if isolation is critical) → `test-driven-development`, `frontend-design` (UI work only) | code on a `feat/*` branch, one task at a time | **GATE — compact in-session plan per task** |
| 5 QA | `test-driven-development`, `run`, `verify` (`webapp-testing` for UI/browser) | tests green, app runs, CI green | proceed (disclose results) |
| 6 Review | `code-review`, `simplify`, `definition-of-done-review` — pick what the change warrants | clean diff, findings fixed | inline, no gate — but **`security-review` is mandatory if a sensitive area is touched** |
| 7 Land | `project-status` | PR opened where hosting supports it. Without PR support, the branch is pushed if a remote exists, any available CI runs, and the human merges it directly; with no remote, the human merges the local branch ([Rules](#rules) → Tracker, remote, and PR/CI capabilities). **GitHub:** the PR carries `Closes #N` and the issue closes on merge — nothing to write. **Any other tracker or local-only:** no closing keyword; move the task to _in review_ according to [Task completion by tracker](#task-completion-by-tracker) | **GATE — the human merges** |
| 8 Retro | reflect + write (native) | curate **0–3** durable learnings after every task; after the final child, reconcile feature artifacts and the parent epic (see [Stage 8](#stage-8-what-a-learning-is-and-isnt)) | if repository files changed, offer to land them on `main`; otherwise continue without an empty landing action |

## Gate protocol (non-negotiable)

At every **GATE**, do ALL of the following and then halt:
1. Name the artifact you produced and its path. For the Stage 4 plan, follow `feature-start` for its
   compact in-session format; no file path exists unless the human requested a durable plan.
2. Summarize what's in it in 2–4 lines.
3. Say exactly what the next stage will do.
4. Ask: "Approve to proceed, or tell me what to change?" For bootstrap, Stage 0a approval does not
   ask for a commit; at the Stage 0b foundation gate, ask to land the full context + foundation
   package on `main`. For adoption, ask to land the reconstructed package at the combined Stage 0
   gate. Stage 1 approval also does not ask for a commit; the approved PRD stays in the worktree
   while Stage 2 produces the ADRs, architecture, security notes, and frozen contract. At the Stage
   2 gate, ask to commit the full Stage 1–2 planning package to `main` before decomposition. These
   requests satisfy the don't-commit-unless-asked guardrail; skip them and Stage 4's clean-tree
   check blocks the branch. Stage 3 Decompose is **not** a gate — never stop there. Tracker-backed
   it writes only issues; local-only it writes `docs/progress.md`, so just **disclose** that the file
   is uncommitted and continue. `feature-start` clears it at the Stage 4 gate, where stopping belongs.

Do not run the next stage's skill until the user approves. Skills are guidance injected into
context — only YOU enforce these stops, so be explicit every time.

**Gates vs. proceed-with-disclosure.** Only the **GATE** rows are hard stops: Foundation, Spec,
Architecture+Contract, the per-task Implement plan, and the human merge at Land. The remaining
stages (Decompose, QA, Review) are **proceed-with-disclosure**: do the work, then state what you
did and any decision a human might want to override, and continue — don't wait. The human can
always interrupt. This keeps the front half rigorous and the back half moving.

**The Stage 5 CI seam — don't over-stop.** When CI exists and needs a pushed branch, the guardrail
says don't commit/push/PR unless asked. That is **one narrow stop at the commit/push boundary — not
a reason to stop at the end of Stage 4.** After the Implement plan gate, keep going through
everything that needs _no_ push: local tests, `run`/`verify`, and the whole Stage 6 pass
(`code-review`, `simplify`, `security-review` if sensitive, diff hygiene). Only _then_ stop, at the
push, and disclose: _"local checks + review done; CI green is pending your approval to commit/push."_
After approval, start CI and return to the human merge gate instead of polling; required CI must be
green before the human merges. If no CI workflow exists, CI is N/A and no push is required for it.

## Task completion by tracker

**This is the canonical statement — other kit docs point here rather than restating it.**

**`Closes #N` is GitHub-only syntax.** On Linear/Jira it either fails to close the real task or
closes an unrelated repo issue of that number — unless _that tracker's own_ Git integration is
configured, which auto-closes via its native key (`ENG-123`, `PROJ-45`) instead, same mechanism as
GitHub's, different syntax. A **local-only** id is a `docs/progress.md` row, not an issue at all, so
nothing auto-closes. So:

- **GitHub** — the PR carries `Closes #N`, the issue stays **open** through Land, and merging closes
  it. Never close it by hand (move a board column only if the project has one).
- **Linear/Jira with Git integration configured** — reference the native key per that integration's
  convention (commit/PR title, or branch name); it closes the issue on merge like GitHub. Confirm the
  integration is actually wired before relying on it — don't assume.
- **Linear/Jira with no Git integration, or local-only** — **no closing keyword anywhere**, in the PR
  or in commits. The task moves to _in review_ at Land and is completed only after the merge.

**Who writes the tracker.** Against an **external tracker** `project-status` is read-only — it
never edits issues unless the user explicitly asks — so a Linear/Jira transition is a separate,
outward-facing action: show the change and get a go-ahead before writing. In **local-only**,
`docs/progress.md` _is_ the tracker and `project-status` maintains it (its one documented write);
that's a repo file, so the edit rides the normal commit approval. Either way the transition is
never a silent side effect of opening the PR — if it hasn't happened, report the tracker as stale
rather than describing it as moved.

**After the merge — close the loop before Retro.** Some tracker work can only happen once the code
lands, so the pipeline doesn't end at the merge gate. When the human confirms the merge: **GitHub**
has closed the issue itself — nothing to do. **Linear/Jira with Git integration configured** has
also closed it via the native key — verify it actually fired, don't assume. An **alternate tracker
with no Git integration** needs its task closed explicitly now — outward-facing, so confirm before
writing, same as at Land.
**Local-only** needs the `docs/progress.md` row moved to `Done` —
and that file _is_ the tracker, so **check out the default branch and sync it first**: you're still
standing on the just-merged `feat/*`, and committing there strands the update on a dead branch while
`main` reads _In review_ for good. Then edit and ask to commit; if `main` is PR-protected, land it
via a `plan/*` branch → PR like any other doc. Stage 8's learnings can ride the same commit.

Never pre-empt any of this before the merge: until the human merges, the honest state is *in
review*, and an abandoned or rejected PR must not leave a task reading done.

## Stage 8: Per-task learning, final epic reconciliation

After the merge, complete the task transition under [Task completion by tracker](#task-completion-by-tracker),
then run the Retro learning pass after every landed task using the criteria below. The budget remains
**0–3** durable learnings per task, and writing nothing remains normal.

First check whether the landed task completes its enclosing feature or epic. If child tasks remain,
do not reconcile feature artifacts or update the parent epic checklist. A decision, contract change,
security correction, or document required by the next task should have landed with the task PR. If
one is discovered only after merge, correct it before the next task; that is blocking corrective
work, not routine reconciliation.

If a leaf-task learning, local-only tracker transition, or blocking correction changes a repository
file, check out and sync the default branch, then ask to land the edit there. If the default branch
is protected, use a `plan/*` branch and the normal review path. Do not invoke `feature-start` until
those edits are on the default branch and the worktree is clean. If the leaf-task Retro produces no
repository edit, continue to the next task without a landing action.

When all child tasks are complete, reconcile the feature's durable artifacts with what actually
shipped. Read the PRD, ADRs, frozen contract, architecture, security, test strategy, and tracker.
Include `docs/contracts/README.md` when it names or indexes the contract source. Update stale
lifecycle labels and status fields: Draft, Proposed, Approved, Accepted, Final, Current, In review,
Done, or the local template's equivalent.

Also reconcile the parent epic: verify every child is complete, update its task checklist, and
confirm the epic Definition of Done and end-to-end acceptance criteria. **Local-only:** make the
checklist and `Done` transition in `docs/progress.md` part of this repository reconciliation.

Check out and sync the default branch before editing; the final task's learning, artifact
reconciliation, and local-only tracker transition may share one landing action. Land all final
reconciliation repository edits on the default branch before completing the parent epic. If that
requires a `plan/*` PR, wait for the human to merge it and confirm the edits are on the default
branch. Only then update an external tracker: **GitHub:** the child PRs close only their task
issues, so ask for approval to update and close the parent issue explicitly. **Another external
tracker:** verify whether its integration completed the parent; if not, ask before updating and
closing it. Treat a local-only epic as complete only after its `docs/progress.md` transition has
landed. Do not report the epic done or offer `improve` until its authoritative tracker record is
complete.

If implementation drifted from the approved PRD, ADRs, or frozen contract, do not hide the drift by
rewriting history. Record the shipped state in the artifact that owns it. A changed decision needs a
new ADR; a changed shipped contract needs the versioning or deprecation decision required by
`AGENTS.md`. Ask before broadening the feature beyond the approved scope.

## Stage 8: what a learning is (and isn't)

`docs/context.md` is loaded at the **start of every session, forever**. A line you add there is a
permanent tax on every future task — so the retro's job is **curation, not transcription**. Writing
nothing is a normal, frequent outcome; a smooth task teaches nothing durable.

A learning qualifies only if a future agent would **do the wrong thing without it**: a non-obvious
trap, a tool/library behavior that contradicts its docs, a constraint discovered the hard way. If
it lives somewhere else, it goes there instead — **never both**:

| Tempting to write | Where it actually belongs |
|---|---|
| What shipped / summary of the change | the PR + git history (already permanent) |
| Why we chose X | an ADR |
| How the system is now shaped | `docs/architecture.md` |
| What's next / next slice | the tracker (goes stale here within days) |
| How we test this layer | `docs/test-strategy.md` |
| Review/process meta ("Codex was right", "retro lands on main") | nowhere — drop it |

**Format — enforced, not suggested:** append to the flat `## Learnings` list as **one dated bullet,
≤3 lines**, stating the trap and the rule. No per-feature `###` headings, no
"What shipped / Keep doing / Watch out for / Process" sub-structure — that's a retro _report_, not
durable context. Budget: **0–3 bullets per retro.** If you're writing a fourth, you're transcribing.

**Prune before you append** (this is the part that keeps the file from growing unbounded): delete
bullets whose gotcha is now fixed, fold any that a doc/ADR/contract now covers into that doc, and
**rewrite superseded bullets in place** rather than appending a contradicting one. Keep the whole
section under ~30 bullets — at the cap, earn each new line by removing one.

**Surface `improve` only when this retro completes an epic-level group.** Check the tracker before
closing Stage 8. Do not surface these options after a leaf-task retro, or after a small parent task
whose purpose is only to organize implementation subtasks. If the enclosing epic-level group still
has unfinished work, name the next task and return to the Stage 4 plan gate. "Epic-level" is the
portable concept, not a required tracker type: it may be a Jira Epic, Linear Project, GitHub
milestone/parent issue, or local `docs/progress.md` section that represents the larger product
outcome containing multiple implementation tasks. If there is no such enclosing group, skip the
`improve` recommendation.

After an epic completes:

> Epic {key} done. Optional:
> 1. `improve`, scoped to what this epic touched, to audit what just shipped.
> 2. `improve next` to surface directions only; after choosing one, decline its planning step and
>    start `sdlc {chosen direction}`.
> 3. Start the next feature with `sdlc {feature}`.

This is disclosure, not a gate. `improve` is an optional third-party companion skill (see
`required-skills.yml`) — never required, never auto-run; naming it here just removes the guesswork.
State the scope in prose, as above: `next` is a real invocation variant, but there is **no
epic/issue flag** — don't advertise one, or you promise scoping the skill won't honor.
When a chosen direction returns to `sdlc`, route it through Stage 1; never accept an `improve`
design or spike plan as a substitute for this pipeline's PRD path.

## Rules

- **GitHub Flow:** `main` is always deployable. Work on short-lived `feat/{issue#}-{slug}`
  branches → PR → merge → deploy. Environments are deploy targets, not long-lived branches.
- **Tracker, remote, PR workflow, and CI workflow are independent capabilities.** _Local-only_ means
  `docs/progress.md` replaces an **external tracker** — it does **not** imply there's no remote, and
  such a project can still open PRs and run CI. Equally, a remote does **not** imply a PR workflow:
  a bare, self-hosted, or backup remote has no PRs, branch protection, or checks to honour. Decide
  on what the hosting _actually supports_, never on remote presence as a proxy:
  - **PR workflow available** → open the PR; run CI there when a CI workflow also exists, then the
    human merges through the PR. If no CI workflow exists, the CI check is N/A.
  - **No PR workflow, CI workflow available** → push the branch to start CI, require it to be green,
    then the human merges `feat/*` into `main` directly.
  - **No PR or CI workflow** → the human merges `feat/*` into `main` directly; push the branch only
    if a remote exists.
  - **A configured PR or CI workflow is unreachable** (expired auth, network) → a **blocker, not a
    mode**: required checks and branch protection must not be routed around. Surface the fix
    (`gh auth setup-git`; see `AGENTS.md` → Guardrails) and stop.

  The merge gate is unchanged in every case — never treat a missing capability as licence to skip
  it, and never invent a remote to satisfy the flow.
- **Default to a feature branch.** Use a git worktree (`using-git-worktrees`) only when isolation
  is genuinely critical — parallel or disposable work — not as the default.
- **Planning commits land on `main`.** Stage 0 foundation artifacts may be committed after the
  foundation gate. For a feature, keep the approved Stage 1 PRD in the worktree, then commit the
  Stage 1–2 planning package once after Stage 2 approves the ADRs, architecture/security updates,
  and frozen contract. Stage 4 branches from a clean `main` that already holds the frozen contract —
  only code lives on the `feat/*` branch. If `main` is PR-protected, use a `plan/*` branch → PR →
  merge, then branch `feat/*`. **Stage 8 retro learnings** (`docs/context.md`) land on `main` the
  same way before the next task or feature branch; final feature reconciliation waits for the last
  child. (See `AGENTS.md` → Where planning commits land.)
- One feature in flight per branch. Reference the tracker issue (its `#`/key) in commits/PRs.
- At Decompose, create issues with `gh issue create` and **shape their bodies to match**
  `.github/ISSUE_TEMPLATE/{epic,task}.md` — one `epic` per feature, a `task` per child. (`--body`
  bypasses the template, so follow its structure by hand: reference line → Scope/Tasks → DoD.)
  Another tracker: its create call. Local-only: add one feature/epic row and its child task rows to
  `docs/progress.md`; put the feature key in each task's `Parent` column. Number the task rows in
  their `#` column, since that number is the task's identifier for the rest of the pipeline (Stage 4
  branches `feat/{id}-{slug}` from it).
- **Definition of Ready** before Stage 4: acceptance criteria written, contract frozen, no open
  questions. **Definition of Done** before Land (Stage 7) (see `AGENTS.md`).
- Contract-first: never let implementation drift from the frozen contract. Changing a shipped
  contract requires a new ADR (versioning/deprecation).
- **Reviews run inline** during Implement/QA — pick `code-review` / `simplify` /
  `definition-of-done-review` as the change warrants. `security-review` is **mandatory** (not
  agent-discretion) whenever a sensitive area is touched.
- Sensitive areas (canonical list in `AGENTS.md` → Sensitive areas): threat-model at Stage 2
  (`docs/security.md`) AND `security-review` at Stage 6.
- DB schema changes follow expand/contract (migrate → deploy → clean up) **once the table holds real
  data or any deployed process reads or writes it** — a deployed _writer_ breaks on a renamed/dropped
  column or a new required one just as a reader does. Before that, change it outright.
- If a PRD/ADR is ambiguous, stop and ask — do not guess.
- Keep the relevant doc (`architecture.md` / ADR) updated as you go; task status lives in the
  tracker (no in-repo mirror), reported via `project-status`.
- **At Land, don't poll CI.** With a PR workflow, open the PR and report CI running; with CI but no
  PR workflow, push the branch to start CI and report the run. A _single_ status glance to catch an
  instant failure is fine. Then **stop — return to the human merge gate.** Don't watch the run to
  completion (`gh run watch`) or keep the turn alive polling. Required CI must be green before the
  human merges; a later failure is handled as a normal fix, not babysat in the Land turn.
- Don't commit, push, open PRs, **or merge** unless asked — **merge is always the human's call.**

## Referenced files

- Operating manual + Definition of Done: `AGENTS.md`
- Templates: `docs/` (context, `prd/0000-product.md`, prd, adr, architecture, contracts,
  security, briefs, progress, test-strategy, runbook)
- Custom skills: `feature-start`, `project-status`, `definition-of-done-review`
