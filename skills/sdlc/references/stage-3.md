# Stage 3 — Decompose

Read this before any Stage 3 work. Tracker capabilities and mechanics live in
`references/rules.md`; whether this stage stops or proceeds is the router's gate table.

## Output

Tracker tasks for the feature — one epic/parent per feature, one task per child:

- **GitHub (default):** create issues with `gh issue create`, shaped per
  `.github/ISSUE_TEMPLATE/{epic,task}.md`. `--body` bypasses the template, so follow its structure
  by hand: reference line → Scope/Tasks → DoD.
- **Another external tracker:** its native create call and issue types.
- **Local-only:** add one feature/epic row and its child task rows to `docs/progress.md`; put the
  feature key in each task's `Parent` column. Number the task rows in their `#` column — that
  number is the task's identifier for the rest of the pipeline (Stage 4 branches
  `feat/{id}-{slug}` from it).

The tracker is the record — no in-repo mirror. `project-status` reports the breakdown after
decomposition.

## Skills

- `writing-plans` — use its decomposition method; write the result to the tracker. Do **not**
  create `docs/superpowers/plans/`; the tracker is the record.
- `project-status` — reports the breakdown.

## After the breakdown

Disclose: the epic, its child tasks in build order, and where the record lives. Local-only mode
writes `docs/progress.md`; disclose that the file is uncommitted — it lands with the task work's
normal commit approval at the CI seam (`references/rules.md`).
