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
  datastore, API style), the **architecture skeleton**, **foundational threat model**, and **core
  contract**. These belong to no single feature.
- **Feature-level** — produced per feature (Stages 1–8): a brief, a feature PRD, feature ADR(s),
  and a contract _slice_.

Don't design every feature up front — but DO lock the handful of foundational decisions a first
feature can't start without. Let everything else emerge per-feature.

## First: orient

**Resolve skills from the skill dirs.** Project-local bundled skills are authoritative inside a
pipeline project. Use the project's local skill first; consult user-global directories
(`~/.agents/skills`, `~/.claude/skills`) only when that local skill is absent, and disclose the
fallback. If neither location has it, use your **runtime's equivalent** — several stage skills are
named after Claude Code's commands (`code-review`, `simplify`, `security-review`) and other
runtimes have their own equivalents (e.g. Codex `review` ≈ `code-review`). Only when no skill or runtime
equivalent exists should you use the manual `fallback` in `required-skills.yml`.

1. Read `AGENTS.md`, `docs/context.md`, and `docs/test-strategy.md`. **Stage 0 is incomplete** if
   the operating manual or context is missing, `AGENTS.md` still contains `Stack (placeholder`, the
   context still has its `> STATUS: TEMPLATE` line or `{placeholder}` tokens, or the context lacks
   populated `## Lifecycle` and `## Production register` sections with current values, triggers, and
   owners, or the test strategy is missing or still contains its `STATUS: TEMPLATE` marker or
   placeholder tools.
   Stage 0 is also incomplete when the product PRD, architecture, contracts index, or foundational ADR set is missing or still templated.
   A missing or templated security threat model also blocks completion. Check
   `docs/prd/0000-product.md`, `docs/architecture.md`, `docs/security.md`,
   `docs/contracts/README.md`, and the applicable decisions in `docs/adr/`; reject placeholder tokens, example-only contract paths, draft foundation status,
   and an ADR directory that records no actual stack, repository, auth, datastore, or API decision.
   Also reject a security doc with no project-specific foundational threats and mitigations. The
   installer pre-creates these
   paths, so do NOT rely on existence alone. If Stage 0 is incomplete, run
   the on-ramp and treat **"context filled" as a gate** — do not advance to Discovery until the
   STATUS marker is gone and the sections are completed for this project:
   - **`bootstrap` (new project, little/no code):** two parts —
     - **0a Context:** the kit's installer already scaffolded `docs/`, `AGENTS.md`, and the
       one-line `CLAUDE.md` pointer — if any are missing, re-run the kit's `install.sh` (it's
       non-destructive) rather than recreating them by hand. Then adapt the stack and conventions in
       `AGENTS.md` and interactively fill `docs/context.md`. _Gate: context filled._
     - **0b Foundation:** produce the **project-level** artifacts — a product PRD at
       `docs/prd/0000-product.md`, the few unavoidable cross-cutting ADRs (stack, repo layout,
       auth, datastore, API style), the `architecture.md` skeleton, a core contract scaffold, the
       foundational threat model in `docs/security.md`, and configure `docs/test-strategy.md` with
       the real test tools. Keep it minimal: only decisions a
       first feature genuinely can't start without — let the
       rest emerge per-feature. **GATE: approve the foundation before Discovery.**
   - **`adopt` (existing codebase):** use `improve-codebase-architecture` plus explicit read-only
     code analysis to reconstruct `docs/prd/0000-product.md`, reverse-engineer `docs/context.md` +
     `docs/architecture.md`, adapt `AGENTS.md` to the actual stack and conventions, and configure
     `docs/test-strategy.md` from the existing test setup, reconstruct `docs/security.md` for
     sensitive existing surfaces, and **backfill the foundational ADRs** (stack, repo, auth,
     datastore already baked into the code). That reverse-engineered set IS
     the project-level foundation. Record known **tech-debt / risky areas** and actionable follow-up
     candidates in `architecture.md`; do not create issues during adoption. Stage 3 owns issue
     creation after foundation approval. Your first workflow-validation feature starts at Stage 1.
     **GATE: approve.**
   - **If these files already exist** (`AGENTS.md`/`CLAUDE.md`/`docs/`), do NOT overwrite. Merge:
     back up or section-merge, preserve the team's content, surface conflicts. Never clobber.
2. **Right-size the path.** Classify the change before routing:
   - **Feature / user-facing / risky** → establish Stage 0 once if needed, then run Stages 1→8.
   - **Bug fix / small enhancement** → **Implement → QA → Review → Land → Retro** (Stages
     4→5→6→7→8; reference an issue; no PRD/contract/ADR).
   - **Chore / docs / dep bump** → **Implement → Review → Land → Retro** (Stages 4→6→7→8;
     trivial diff, CI green before merge).
   - The moment a "small" change touches a **contract**, a **security-sensitive area**, or makes
     a **decision**, it graduates to the full path. When unsure, ask.
3. Read the tracker (via `gh` / `project-status`) and the active PRD to infer the current stage and
   feature (local-only mode: read `docs/progress.md`).
4. State the chosen path, current stage, and next action to the user before proceeding.

## Status header (every response)

Open every response while a feature is in the pipeline with one compact line, so the user — and
you — always know where the pipeline is:

`SDLC ▸ Stage {N}/8 {Name} · {next gate or action}`

Examples (on-ramp sub-stages keep their letter — `0a`/`0b`/`0adopt`):

- `SDLC ▸ Stage 0b/8 Foundation · next gate: approve foundation`
- `SDLC ▸ Stage 1/8 Spec · next gate: approve PRD`
- `SDLC ▸ Stage 4/8 Implement · task #5 · next: plan approval`
- `SDLC ▸ Stage 6/8 Review · running security-review (sensitive area)`

One line only. It doubles as your own anchor — restating the stage each turn is what keeps you from
drifting off-process over a long conversation.

## Borrow the technique, not the workflow

The community skills below are **techniques**, not the pipeline. Each was authored standalone and
carries its own opinions about _where it writes_ and _what it does next_ — those opinions are wrong
here, because **this conductor owns the workflow.** When you run a borrowed skill, use its method
and **override its workflow**:

- `brainstorming` → use its discovery method (explore → **one question at a time** → approaches →
  design), but land the artifact as the **(optional) Stage-1 brief** at `docs/briefs/NNNN-{slug}.md`
  and STOP. Reach for brainstorming + a brief only when the idea is fuzzy; a well-understood feature
  skips both and goes straight to `to-spec`.
  Discovery is exploratory — **no code.** Do **not** write to `docs/superpowers/specs/`, and do
  **not** auto-run `writing-plans`; the next step is the Stage 1 Spec (`to-spec`), then the gate. If
  the user approves its visual companion, set `SUPERPOWERS_DISABLE_TELEMETRY=1` to block its branding
  request. Keep it on loopback; use an SSH tunnel, never plaintext non-loopback mode. Use the default
  temporary session directory; do not pass `--project-dir`. Ignore its instruction to commit or write
  under `docs/superpowers/`; this conductor owns the artifact and approval gate.
- `to-spec` → use its synthesis method and the kit's PRD template, but write the result to
  `docs/prd/NNNN-{slug}.md`; do not publish or label a tracker issue. Tracker work begins at Stage 3.
- `grilling` → use its interview method at **Stage 1 and Stage 2**. Point it at the decision, not the
  document: at Stage 2 the subject is the architecture and the contract shape about to freeze, and it
  runs before that gate.
- `documentation-and-adrs` → ADRs go to **`docs/adr/NNNN-{slug}.md`** (this project's convention),
  never `docs/decisions/`.
- `writing-plans` → use its decomposition method at Stage 3, but write the result to the tracker.
  Do **not** create `docs/superpowers/plans/`; the tracker is the record.
- `ponytail` → use only for backend/domain logic, parsers, transformations, state management,
  tooling, and dependency choices. It cannot override contracts, security, accessibility, explicit
  requirements, or proportional verification; its one-check rule is a minimum, never a cap.
- `improve-codebase-architecture` → use only its code-reading and deepening heuristics. In that
  snapshot, `CONTEXT.md` means `docs/context.md`; do not invoke the unavailable `codebase-design` or
  `domain-modeling` skills. Update `docs/context.md` directly when needed, and skip its upstream HTML
  report. Write the adoption findings into this kit's foundation artifacts instead.
- Worktree isolation is an explicit manual escape hatch for parallel or disposable work, never the
  default. The operator supplies and verifies a private, new or empty path outside every checkout.
  Use the generic Git-only `git worktree add` and non-forced `git worktree remove` guidance in
  `feature-start`; the kit does not enforce platform-specific path safety.
- `webapp-testing` → use its Playwright method, but do not use its bundled `with_server.py`; use the
  project's lifecycle runner or an already-running server so output is drained and the full process
  tree remains owned. Wait for an app-specific readiness signal, such as a locator, URL, or health
  check; do not require `networkidle`.
- Any skill that wants to open tracker issues/epics → **defer to Stage 3 Decompose.** The Spec stage
  produces a PRD, not issues.

If a borrowed skill's default fights an `AGENTS.md` convention, **`AGENTS.md` wins.**

## Communication and documentation writing standards

Follow the communication and documentation writing standards in `AGENTS.md`; it is the single source
for both. Apply `unslop` automatically to human-facing replies and prose where applicable; follow its
canonical scope and exclusions. Trim borrowed-skill output to match before each gate.

Before presenting gate artifacts, tracker issues, or PR text, review each point against the
one-point writing rule in `AGENTS.md`. Split independently actionable obligations without losing
conditions or changing requirement IDs. This is an editorial review, not a sentence-count test;
keep document structure and PRD/ADR introductions intact.

## The stages, skills, and gates

| Stage | Use skill | Output | After producing output |
| ------- | ----------- | -------- | ------------------------ |
| 0a Context (new) | installer-scaffolded templates (fill) | `AGENTS.md`, filled `docs/context.md` | **GATE — context filled** |
| 0b Foundation (new) | `documentation-and-adrs` | `docs/prd/0000-product.md`, foundational ADRs (→ `docs/adr/`), `architecture.md` skeleton, core contract scaffold, foundational threat model in `docs/security.md`, configured `docs/test-strategy.md` (**trim `docs/contracts/README.md`** to real/`(future)` paths — never leave template examples) | **GATE — approve foundation** |
| 0 adopt (existing) | `improve-codebase-architecture` + read-only code analysis | reconstructed product PRD, context/architecture/security, configured `docs/test-strategy.md`, and backfilled foundational ADRs (**point `docs/contracts/README.md` at the existing contract source**; note tech-debt/risks in `architecture.md`) | **GATE — approve** |
| 1 Spec | `brainstorming` (method only) → `to-spec` → `grilling` | **optional** Stage-1 brief `docs/briefs/NNNN-*.md` (only for a fuzzy/speculative idea — else skip straight to the PRD), then hardened PRD `docs/prd/NNNN-*.md` (no issues yet) | **GATE — approve PRD** |
| 2 Architecture + Contract | `documentation-and-adrs` + `grilling` | ADR(s) in `docs/adr/`, updated `docs/architecture.md`, `docs/security.md` (sensitive areas), **frozen** contract artifact in repo (OpenAPI/tRPC/schema) | **GATE — approve approach + freeze interface** |
| 3 Decompose | `writing-plans` + `project-status` | **tracker issues** (GitHub by default) shaped per `.github/ISSUE_TEMPLATE/{epic,task}.md` (the tracker is the record — no in-repo mirror; other trackers: their native issue types; local-only: feature + task rows in `docs/progress.md`) | disclose the breakdown, then continue |
| 4 Implement | `feature-start` (direct feature branch by default; manual Git-only worktree escape hatch), `frontend-design` (UI work only), `ponytail` (backend/domain logic, parsers, transformations, state, tooling, and dependency choices) | code on a `feat/*` branch, one task at a time | **GATE — compact in-session plan per task** |
| 5 QA | proportional local verification + runtime-equivalent checks (`webapp-testing` for UI/browser) | change-scope evidence; CI green now or after PR creation | proceed (disclose results) |
| 6 Review | mandatory `code-review`, `simplify`, and local-readiness `definition-of-done-review` | clean diff, local DoD evidence, findings fixed | inline, no gate — but **`security-review` is mandatory if a sensitive area is touched** |
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
   2 gate, ask to land the full Stage 1–2 planning package on `main` before decomposition, using the
   remote-state landing action in [Rules](#rules) → Default-branch landings. Before
   asking to land a Stage 0 or Stage 2 package that touches a sensitive area, update
   `docs/security.md` and run `security-review` on that planning diff, completing
   [the coverage check](#security-review-coverage). Stage 6 reviews the later
   implementation diff again. These requests satisfy the don't-commit-unless-asked guardrail; skip
   them and Stage 4's clean-tree
   check blocks the branch. Stage 3 Decompose is **not** a gate — never stop there. Tracker-backed
   it writes only issues; local-only it writes `docs/progress.md`, so just **disclose** that the file
   is uncommitted and continue. `feature-start` clears it at the Stage 4 gate, where stopping belongs.

Keep this protocol concise. State the artifact, decision needed, and next action. Do not append a
second explanation of routine permissions, merge ownership, CI polling rules, or other standing
guardrails. Report a deviation or blocker when one exists; otherwise follow the guardrail silently.

Do not run the next stage's skill until the user approves. Skills are guidance injected into
context — only YOU enforce these stops, so be explicit every time.

**Gates vs. proceed-with-disclosure.** Only the **GATE** rows are hard stops: Context, Foundation,
Spec, Architecture+Contract, the per-task Implement plan, and the human merge at Land. The remaining
stages (Decompose, QA, Review) are **proceed-with-disclosure**: do the work, then state what you
did and any decision a human might want to override, and continue — don't wait. The human can
always interrupt. This keeps the front half rigorous and the back half moving.

**The Stage 5 CI seam — don't over-stop.** When CI exists and needs a pushed branch, the guardrail
says don't commit/push/PR unless asked. That is **one narrow stop at the commit/push boundary — not
a reason to stop at the end of Stage 4.** After the Implement plan gate, keep going through
everything that needs _no_ push: proportional local checks, runtime observation, and the whole Stage 6 pass
(`code-review`, `simplify`, `security-review` if sensitive, diff hygiene). Only _then_ stop, at the
push. For a PR workflow, report that tree-only local checks and review are done, then ask one combined
question: _"Approve commit, push, and opening the PR?"_ With a remote but no PR workflow,
ask _"Approve commit and push?"_ With no remote, ask only _"Approve commit?"_ After approval, create
the commit first, verify its parent and tree, and rerun every metadata- or topology-dependent check
against that commit. If any check fails, stop before the push. When they pass, push or open the PR
and start CI when available, then follow the Land rules below. If no CI workflow exists, CI is N/A.

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
`main` reads _In review_ for good. Then edit and land it by remote state ([Rules](#rules) →
Default-branch landings). Stage 8's learnings can ride the same commit.

Never pre-empt any of this before the merge: until the human merges, the honest state is _in
review_, and an abandoned or rejected PR must not leave a task reading done.

## Artifact lifecycle

At Stage 2, put approved future changes in a separate planned-changes section of architecture and
security docs; do not rewrite the current system as though the design were implemented. PRD approval,
ADR acceptance, and contract freeze are decision states. Track implementation separately using
Not implemented, Partially implemented, or Implemented. Keep one delivery summary with links to the tracker and
verification evidence, not another task checklist. Update affected current-behavior claims with
each implementation task; full feature reconciliation still belongs to the final Retro.

Compatibility artifacts, deprecation notes, and migration guidance in current-state docs describe an
active transition someone has to make. Use the specific Lifecycle trigger in `docs/context.md`: while
its condition is absent, state the current shape and record the deferral in the production register;
when it is present, include and verify the transition before promotion.

**Amending a decision mid-implementation.** An ADR or PRD states current intent; it is not authority
for its own sake. When implementation shows a recorded decision is wrong, amend the record rather
than building around it, in the same change as the code and never as a silent divergence. Edit a
Proposed or Accepted ADR in place only while it is unimplemented and dependency-free. After amending
an accepted ADR, renew human approval and re-freeze any affected contract before implementation
resumes. For an implemented or depended-on ADR, add a superseding ADR, renew human approval before
implementation resumes, re-freeze any affected contract, mark the old one `Superseded by ADR-NNNN`,
and name the assumption that turned out false rather than the alternative looking simpler. The
artifact class decides the route: an internal ADR follows this matrix; a shipped contract with a
deployed consumer needs the versioning or deprecation decision in `AGENTS.md`, while one without a
deployed consumer may change outright under this matrix with applicable approval and re-freeze. Every
PRD requirement or scope amendment returns to human approval. A reversal that invalidates the rest of
the plan belongs at the plan gate, not absorbed into the diff. If you cannot say why the old decision
was wrong, the objection is probably inconvenience.

## Security-review coverage

For every required planning or implementation security review, establish the intended file scope
before invoking a tool. Include the relevant PRD, ADRs, contracts, architecture, threat model,
implementation, and tests, including staged, unstaged, and new/untracked artifacts. Record the base
and reviewed revision or content identity; do not stage or commit files merely to make them visible.

Compare the tool's actual file coverage with that scope. Filtered Markdown, tests, untracked files,
an empty result, or unknown coverage do not count as reviewed. Read omitted files directly and
perform the structured manual review in `required-skills.yml`; record each file as tool-reviewed,
manually reviewed, or excluded with a scope-specific reason. Exclusions cannot waive relevant
sensitive changes. If required content is inaccessible, report incomplete coverage and block the
planning landing or implementation readiness, rather than returning a clean verdict.

Record coverage and verification limits in `docs/security.md` using its review-record fields.
After substantive edits, refresh the affected review and its coverage identity. A planning review
certifies the design only, never runtime enforcement. This check applies even when a tool reports
no findings; no particular agent runtime is required.

## Stage 8: Per-task learning, final epic reconciliation

After the merge, complete the task transition under [Task completion by tracker](#task-completion-by-tracker),
then run the Retro learning pass after every landed task using the criteria below. The budget remains
**0–3** durable learnings per task, and writing nothing remains normal.

First check whether the landed task completes its enclosing feature or epic. If child tasks remain,
do not perform full feature reconciliation or update the parent epic checklist. A decision,
contract change, security correction, or document required by the next task should have landed
with the task PR. So should corrections to current-behavior claims in architecture and security
docs under [Artifact lifecycle](#artifact-lifecycle); this is not a second task-status tracker. If
one is discovered only after merge, correct it before the next task; that is blocking corrective
work, not routine reconciliation.

If a leaf-task learning, local-only tracker transition, or blocking correction changes a repository
file, check out and sync the default branch, then ask to land the edit there by remote state
([Rules](#rules) → Default-branch landings). Do not invoke `feature-start` until those edits are on
the default branch and the worktree is clean. If the leaf-task Retro produces no repository edit,
continue to the next task without a landing action.

When all child tasks are complete, reconcile the feature's durable artifacts with what actually
shipped. Read the PRD, ADRs, frozen contract, architecture, security, test strategy, and tracker.
Include `docs/contracts/README.md` when it names or indexes the contract source. Update stale
delivery summaries and status fields against evidence. Preserve decision history: an Accepted ADR
or frozen contract does not become implemented merely because it was approved. Distinguish partial
implementation from completed implementation. Keep the tracker authoritative for task status.

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
rewriting history. Record the shipped state in the artifact that owns it. For an ADR, apply the
amendment matrix above: edit a Proposed or Accepted ADR only while it is unimplemented and
dependency-free; after amending an accepted ADR, renew human approval and re-freeze any affected
contract. Create a superseding ADR, renew human approval before implementation resumes, re-freeze any
affected contract, and mark the old one for an implemented or depended-on decision, regardless of its
status. For contract drift, a deployed consumer requires the versioning or deprecation decision
required by `AGENTS.md` before changing the interface; only when there is no deployed consumer may the
ADR matrix route apply, with applicable approval and a re-freeze. Every PRD requirement or scope change
returns to human approval. Ask before broadening the approved scope.

## Stage 8: what a learning is (and isn't)

`docs/context.md` is loaded at the **start of every session, forever**. A line you add there is a
permanent tax on every future task — so the retro's job is **curation, not transcription**. Writing
nothing is a normal, frequent outcome; a smooth task teaches nothing durable.

A learning qualifies only if a future agent would **do the wrong thing without it**: a non-obvious
trap, a tool/library behavior that contradicts its docs, a constraint discovered the hard way. If
it lives somewhere else, it goes there instead — **never both**:

| Tempting to write | Where it actually belongs |
| --- | --- |
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
>
> 1. `improve`, scoped to what this epic touched, to audit what just shipped.
> 2. `improve next` to surface directions only; after choosing one, decline its planning step and
>    start `sdlc {chosen direction}`.
> 3. Start the next feature with `sdlc {feature}`.

This is disclosure, not a gate. `improve` is an optional external skill described in `INSTALL.md`.
It is never required or run automatically. Naming it here removes the guesswork.
State the scope in prose, as above: `next` is a real invocation variant, but there is **no
epic/issue flag** — don't advertise one, or you promise scoping the skill won't honor.
When a chosen direction returns to `sdlc`, route it through Stage 1; never accept an `improve`
design or spike plan as a substitute for this pipeline's PRD path.

## Rules

- **GitHub Flow:** `main` is always deployable. Work on short-lived `feat/{id}-{slug}`
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
- **Before Land, re-evaluate lifecycle triggers.** Compare the intended deployment or promotion and
  candidate Lifecycle and production register with the target baseline recorded by
  `definition-of-done-review` during local readiness.
  Evaluate target rows even if the candidate deletes or weakens them. Treat any candidate Lifecycle
  downgrade from the target baseline as a policy change requiring a durable, human-approved decision
  recorded in the applicable ADR or production register, with factual evidence that the relevant consumer,
  data, or traffic is absent; fulfillment of a deferred row does not itself
  authorize the downgrade. Treat deletion or weakening of a target row or trigger as an additional
  policy change requiring a durable, human-approved retirement decision recording factual evidence
  that the deferred work is fulfilled and verified or that the trigger no longer applies in the applicable
  ADR or production register. Fulfillment evidence may support that decision but does not replace it. If
  the merge reaches a trigger, the deferred work
  must be on the target or included in the
  reviewed landing candidate and verified before promotion; the pre-merge lifecycle state is not
  sufficient to defer it.
- **Default to a feature branch.** Use a git worktree only as an explicit manual escape hatch for
  opt-in parallel or disposable isolation, or when the user requests it. The operator supplies and
  verifies a private, new or empty path outside every checkout; use only the generic Git-only
  guidance in `feature-start`.
- **Default-branch landings (Stage 0, Stage 2, Stage 8).** Planning packages and Retro edits land
  on the default branch, never a feature branch, and the ref Stage 4 cuts from must already hold
  them. Stage 0 foundation artifacts may land after the foundation gate. For a feature, keep the
  approved Stage 1 PRD in the worktree, then land the Stage 1–2 planning package once after Stage 2
  approves the ADRs, architecture/security updates, and frozen contract. Stage 8 retro learnings
  (`docs/context.md`) land the same way before the next task or feature branch; final feature
  reconciliation waits for the last child. Ask for the landing action by remote state:
  - **No remote** → commit to the local default branch.
  - **Remote, default branch unprotected** → commit and push it under the same approval, so the
    shared default branch holds the frozen contract. A commit alone leaves Stage 4 branching from a
    base the remote lacks, folding the planning package into the feature PR.
  - **Remote, default branch protected** → `plan/{NNNN}-{slug}` → PR → merge, then branch `feat/*`;
    wait for the human to confirm the package reached the default branch.
  Stage 4 branches from that clean ref; the branch carries the task implementation plus its
  required task-scoped tests and docs. (See `AGENTS.md` → Where planning commits land.)
- One feature in flight per branch. Reference the tracker issue (its `#`/key) in commits/PRs.
- At Decompose, create issues with `gh issue create` and **shape their bodies to match**
  `.github/ISSUE_TEMPLATE/{epic,task}.md` — one `epic` per feature, a `task` per child. (`--body`
  bypasses the template, so follow its structure by hand: reference line → Scope/Tasks → DoD.)
  Another tracker: its create call. Local-only: add one feature/epic row and its child task rows to
  `docs/progress.md`; put the feature key in each task's `Parent` column. Number the task rows in
  their `#` column, since that number is the task's identifier for the rest of the pipeline (Stage 4
  branches `feat/{id}-{slug}` from it).
- **Definition of Ready** before Stage 4: acceptance criteria written, the applicable contract
  frozen or explicitly N/A for fast-path work with no integration contract, the frozen contract
  matching its accepted ADR and the architecture update, and no open questions.
  Require local readiness before entering Land, then require the full Definition of Done, including
  required CI (see `AGENTS.md`).
- **Every task needs proportional verification, not necessarily a new test.** Start bug fixes with a
  failing automated test or observable reproducer appropriate to the risk; start non-trivial executable
  behavior with a failing test (RED → GREEN). Presentation-only copy, styling, or markup bugs may use
  a failing diff, render, or visual reproducer. Executable validation, authorization or security denial,
  error, retry, timeout, and partial-failure branches need focused automated
  coverage. For documentation changes that affect links or rendering, use link or rendering checks;
  presentation-only docs copy, styling, markup, or attributes may use a diff or one visual check;
  styling, markup, or attributes that change accessibility, security, or interaction behavior need
  focused behavior evidence; for configuration or generated output, use its
  syntax, schema, or generation check. Name the smallest local check that proves the change. For
  shared paths, contracts, or security-sensitive areas, broaden verification to all impacted
  packages/modules; reserve the full suite for broad or high-risk dependency fan-out or an explicit
  project rule. Presentation-only styling, markup, attributes, copy, or layout carry no logic to
  cover; styling, markup, or attributes that change accessibility, security, or interaction behavior
  do and need focused behavior evidence. The external `test-driven-development` skill is an optional
  team-wide policy, not a pipeline dependency.
- **Don't open a browser for a trivial UI change.** A presentation-only markup, copy, or styling
  tweak is proven by the diff or a single visual check, not by a Playwright run or MCP session.
- Contract-first: never let implementation drift from the frozen contract. A shipped contract with a
  deployed consumer requires a versioning/deprecation ADR; if there is no deployed consumer, apply the
  ADR matrix and re-freeze the contract.
- **Reviews run inline** during Implement/QA. Run `code-review`, `simplify`, and local readiness on a
  clean materialization of the complete target-to-tree delta; bind evidence to its target, parent,
  and tree. After commit, require the tree to have the same reviewed content and its parent to match.
  At final confirmation, resolve authoritative target/head tips by PR, remote-only, or local-only
  mode and require a pending non-empty delta. Treat target CI policy as the baseline; feature-side
  changes cannot reduce it, and approved additions or modifications must run from the reviewed
  candidate revision. Accept head CI only when the target is its ancestor; otherwise
  reproduce a synthetic `(target, head)` integration tree and review it against both parents. If
  head or envelope topology differs from landing, accept its CI only for tree-only,
  topology-independent checks; other checks must run on the actual landing candidate. Re-resolve
  tips, policy, and workflow identity before the verdict. Stale refs,
  unreachable configured hosts, changed content, or sensitive interactions block until applicable
  QA and reviews rerun. Classify feature and integration deltas semantically against the canonical
  sensitive-area list and record the rationale. `security-review` is **mandatory** whenever a
  sensitive area is touched.
- Sensitive areas (canonical list in `AGENTS.md` → Sensitive areas): threat-model in
  `docs/security.md` and run `security-review` before landing a sensitive Stage 0 or Stage 2 planning
  package; review the implementation diff again at Stage 6.
- DB schema changes follow expand/contract (migrate → deploy → clean up) **once the table holds real
  data or any deployed process reads or writes it** — a deployed _writer_ breaks on a renamed/dropped
  column or a new required one just as a reader does. Before that, change it outright.
- If a PRD/ADR is ambiguous, stop and ask — do not guess.
- Keep the relevant doc (`architecture.md` / ADR) updated as you go; task status lives in the
  tracker (no in-repo mirror), reported via `project-status`.
- At Land, don't poll CI. With a PR workflow, open the PR and report CI running; with CI but no
  PR workflow, push the branch to start CI and report the run. A _single_ status glance to catch an
  instant failure is fine. Then stop. Don't watch the run to completion (`gh run watch`) or keep the
  turn alive polling. Required CI must be green before merging; once it finishes, run the final DoD
  confirmation before reporting the change ready. A later failure is a normal fix, not babysat in
  the Land turn.
- Don't commit, push, or open PRs unless asked. The human performs every landing merge into the target
  branch. Local default-branch synchronization via `git merge --ff-only` and unreferenced synthetic
  merge/integration commits used only for review evidence are not landing merges. One combined approval
  may cover commit, push, and opening a PR when the request names all three. It authorizes exactly
  the actions named in the request.

## Referenced files

- Operating manual + Definition of Done: `AGENTS.md`
- Templates: `docs/` (context, `prd/0000-product.md`, prd, adr, architecture, contracts,
  security, briefs, progress, test-strategy, runbook)
- Custom skills: `feature-start`, `project-status`, `definition-of-done-review`
