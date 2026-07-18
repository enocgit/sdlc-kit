---
name: project-status
description: >
  Reports where the project stands by reading the live tracker (GitHub Issues/Projects) and
  summarizing it — read-only against external trackers, while local-only mode maintains
  docs/progress.md as the tracker itself. Use when the user asks "what's the project status",
  "where are we on {epic}", "what's next", or wants a Now/Next/Blocked view; also to disclose the
  breakdown after Decompose (Stage 3) or the state after landing a PR (Stage 7).
---

# project-status

Report the current state of the work straight from the **tracker** — GitHub Issues/Projects by
default, the single source of truth. Against an external tracker, this skill **reads and summarizes;
it does not write an in-repo mirror.** There is no `docs/progress.md` snapshot to keep in sync — a
second copy would only drift, so the tracker stays authoritative and always live. In local-only
mode, `docs/progress.md` is the tracker and the skill maintains it as described below.

## Steps

1. **Read the tracker.** Tracker-backed, fetch open/closed issues for the active epic via `gh`
   (e.g. `gh issue list`, `gh project item-list`); if `gh` isn't authenticated, say so and stop.
   **Local-only** (no external tracker), read `docs/progress.md` instead — that's the tracker here,
   so a missing `gh` is expected, not a reason to stop (see Local-only exception below).
2. **Summarize.** Group by epic. Per task show status (Todo / In progress / In review / Done),
   assignee, and linked PR. Give a per-epic completion count and a **Now / Next / Blocked** view.
3. **Flag drift from reality.** Call out anything off — an issue closed without meeting its
   acceptance criteria / Definition of Done, or a PR merged without the docs (`architecture.md` /
   ADR) updated. Report it; don't silently fix it.

## Rules

- **Read-only by default.** Never invent status — read it from `gh`. Don't close/reopen or edit
  issues unless the user explicitly asks; this skill reports.
- **No in-repo mirror.** In tracker-backed mode, do not create or update a `docs/progress.md` — the
  tracker is the record. Keep PRD/ADR/issue cross-links in your summary so it stays navigable.
- **Local-only exception.** If the project runs with no external tracker, `docs/progress.md` *is*
  the tracker (hand-maintained) — read and report from it, and update it there as the source of
  truth. (This is the one case where the skill writes; there's no second copy to drift against.)
