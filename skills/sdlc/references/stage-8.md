# Stage 8 — Retro

Read this before any Stage 8 work. Retro is **the learning pass only** — one small thing after
every merge. Epic closure is a separate, once-per-epic step attached to the final child. The
landing ask forms are restated below (`references/rules.md` stays canonical).

## Learning pass (every merge)

`docs/context.md` is loaded at the start of every session, forever — a line added there is a
permanent tax on every future task. The retro's job is **curation, not transcription**; writing
nothing is a normal, frequent outcome.

**A learning qualifies only if a future agent would do the wrong thing without it** — a non-obvious
trap, a tool/library behavior that contradicts its docs, a constraint discovered the hard way.
Otherwise it belongs somewhere else, never both:

| Tempting to write | Where it actually belongs |
| --- | --- |
| What shipped / summary of the change | the PR + git history |
| Why we chose X | an ADR |
| How the system is now shaped | `docs/architecture.md` |
| What's next / next slice | the tracker |
| How we test this layer | `docs/test-strategy.md` |
| Review/process meta | nowhere — drop it |

**Format — enforced, not suggested:** append to the flat `## Learnings` list as **one dated bullet,
≤3 lines**, stating the trap and the rule. No per-feature headings, no report sub-structure. Budget:
**0–3 bullets per retro**; a fourth means you're transcribing.

**Preserve the guidance comment.** The comment above the `## Learnings` list is the in-file
statement of the format rules — the only format rules an appending agent sees at edit time.
Never delete or rewrite it while editing the section; if a previous pass dropped it, restore it
from the kit template before appending. A learnings list without its guidance comment is how a
list grows unpruned.

**Prune before you append:** delete bullets whose gotcha is fixed, fold any that a doc/ADR/contract
now covers into that doc, rewrite superseded bullets in place. **Promote before you prune:** a
bullet that has now applied across two or more features is a standing rule, not a learning — move
it into `AGENTS.md`, `docs/test-strategy.md`, or an ADR, then delete it from the list. Keep the
whole section under ~30 bullets — at the cap, earn each new line by removing one.

If a learning, local-only tracker transition, or blocking correction changes a repository file:
check out and sync the default branch, then ask to land the edit there. Landing ask, by remote
state: **no remote** → "Approve the retro package — commit to {default branch}?"; **remote,
default branch unprotected** → "Approve the retro package — commit and push to {default
branch}?" under the same approval; **remote, default branch protected** → `plan/{NNNN}-{slug}` →
PR → merge, then confirm. Stage 8's learnings land before the next task or feature branch; a
 declared parallel group gets one learning pass at the group's last merge, before any new work
 starts.

The epilogue lands **directly on the default branch by design, not as a feature PR**: its content
is post-merge fact (delivery record citing the merge, issue closures, shipped-behavior
reconciliation) — a PR cannot carry its own merge's record. The protected-branch PR path is the
only exception, forced by the remote, not chosen for ceremony.

## Epic closure (once, on the final child only)

First check whether the landed task completes its enclosing feature/epic. If child tasks remain:
**stop here** — no reconciliation, no parent-epic updates; name the next task and return to the
Stage 4 plan gate. Corrections to current-behavior claims discovered after merge are blocking
corrective work, not reconciliation — do them before the next task.

When all child tasks are complete:

1. Check out and sync the default branch.
2. Reconcile the feature's durable artifacts with what actually shipped: read the PRD, ADRs,
   frozen contract, architecture, security, test strategy, and tracker; write the narrative's
   **delivery record** (PRD Summary → Delivery) once, true, with evidence links; move any feature
   facts out of planned-changes sections into current-state sections; update stale delivery
   summaries against evidence. Preserve decision history — an Accepted ADR or frozen contract does
   not become implemented merely because it was approved. Keep the tracker authoritative for task
   status.
3. Verify every child sub-issue is closed — the tracker is the record of task state — and confirm
   the epic Definition of Done and end-to-end acceptance criteria. Criteria ticked when their
   proving evidence existed stay ticked if it holds; complete the unchecked remainder here.
   Confirm the `## Learnings` list in `docs/context.md` is within its ~30-bullet cap and prune to
   it. Local-only: make the `Done` transition in `docs/progress.md` part of this reconciliation.
4. Land all reconciliation repository edits on the default branch before completing the parent
   epic (wait for any `plan/*` PR to merge and confirm).
5. Only then update the external tracker: **GitHub** — child PRs close only their task issues, so
   the epic checklist, DoD ticks, and parent close are outward writes. Bundle the whole close-out
   into **one ask** — the reconciliation landing, the epic ticks and close, and any worktree
   disposition — one approval covers the tail; sequence the execution in that order and never ask
   twice after the merge gate. **Another external tracker** —
   verify whether its integration completed the parent; if not, ask before updating. Treat a
   local-only epic as complete only after its `docs/progress.md` transition has landed. Do not
   report the epic done until its authoritative tracker record is complete.
6. Offer the optional next step:

> Epic {key} done. The deep-review cadence expects one full audit per epic (or the project's
> chosen schedule) — per-task review misses what a whole-epic pass catches, and its findings
> enter the pipeline as a plan backlog (Stage 3).
> Optional:
>
> 1. `improve`, scoped to what this epic touched — the default audit implementation.
> 2. `improve next` to surface directions only; after choosing one, decline its planning step and
>    start `sdlc {chosen direction}`.
> 3. Start the next feature with `sdlc {feature}`.

This is disclosure, not a gate. The audit pass is the cadence, not a gate; `improve` itself is an
optional external skill described in `INSTALL.md` and may be substituted by any equivalent
structured review — when it is not installed, use the kit-shipped `improve-codebase-architecture`
read-only audit as the fallback — but the findings route through Stage 3 either way. There is **no epic/issue
flag** — don't advertise one. When a chosen direction returns to `sdlc`, route it through Stage 1;
never accept an `improve` design or spike plan as a substitute for the PRD path.

## Drift, never hidden

If implementation drifted from the approved PRD, ADRs, or frozen contract, record the shipped state
in the artifact that owns it — apply the amendment matrix in `references/rules.md` → Amending
decisions. Ask before broadening the approved scope.
## Next

The pipeline is at rest after the landing. For the next feature, start at Stage 1 — read
`references/stage-1.md` before acting on it.
