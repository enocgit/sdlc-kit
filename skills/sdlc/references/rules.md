# Rules — landing, tracker, and amendments

Mechanics the conductor points to. `AGENTS.md` wins any conflict.

## Landing

Land only after the gate's approval; that approval is the ask. Decide on what the hosting actually
supports, not on whether a remote exists.

**Planning and retro edits** (Stage 0 foundation, Stage 1 proposal, Stage 6 retro):

- **Solo team shape:** the Stage 1 proposal is the first commit on the feature branch and lands with
  the first task's PR. Stage 0 and Stage 6 edits land on the default branch as below.
- **Team shape:** land on the default branch before Stage 3 branches from it:
  - no remote → commit to the local default branch;
  - remote, default branch unprotected → commit and push, under one approval;
  - remote, default branch protected → `plan/{NNNN}-{slug}` → PR → the human merges.

**Code** (Stage 4 → 5):

- PR workflow → push `feat/*`, open the PR; CI runs there; the human merges.
- Remote without PRs → push the branch to start CI; once green, the human merges `feat/*` directly.
- No remote → one combined ask: "Approve commit and merge to the local default branch?" The human
  still owns the decision; execute only after approval.
- No CI workflow → CI is N/A. A configured CI or PR workflow that is unreachable (auth, network,
  quota) is a blocker: surface the fix and stop. If the human merges over it, the PR says the gate
  did not run.

Before reporting a landing done, check every artifact the ask named is in the commit.

## Tracker

- **External tracker (GitHub default):** one issue per task, shaped by `.github/ISSUE_TEMPLATE/`.
  Multi-task changes get an epic with tasks as sub-issues. Creating issues at Stage 2 is the planned
  external write; any later edit, transition, or close is outward-facing and needs an ask.
- **No external tracker:** the proposal's task checklist is the tracker. Tick a task in the commit
  that completes it.
- **One list per change.** `docs/context.md` → Lifecycle names the tracker. When a project adopts
  one midway, update that line; shipped proposals keep their checklists as history. For each open
  proposal, ask, then create issues for its unticked tasks only and replace the checklist with a
  link to the epic. A task never lives in both places.
- **Closing:** `Closes #N` is GitHub-only syntax. Linear or Jira use their own Git integration key
  when one is configured and verified; otherwise write no closing keyword and move the task by hand
  after the merge (ask first). Never mark a task done before its merge.

## Amending decisions

A recorded decision states current intent. When implementation shows it is wrong, amend it in the
same change as the code; never build around it silently.

- **Spec or proposal requirement:** edit it in the change and get human approval before continuing.
- **ADR, unimplemented and nothing depends on it:** edit in place; renew approval.
- **ADR, implemented or depended on:** write a superseding ADR naming the assumption that proved
  false; mark the old one `Superseded by ADR-NNNN`; renew approval.
- **Frozen contract:** re-freeze after approval. A contract with a deployed consumer needs a
  versioning or deprecation ADR.

## Lifecycle

`docs/context.md` → Lifecycle records team shape, deployed consumers, real data, and production
traffic. Rules route on it, so keep it current. The human owns these values: agents propose
updates, never set them silently. When a merge or deployment would trip a production
register trigger, the deferred work lands first. Downgrading a Lifecycle value needs a human-approved
record of the evidence.

## Database schema changes

Use expand/contract (migrate → deploy → clean up) once a table holds real data or any deployed
process reads or writes it. Before that, change it outright.
