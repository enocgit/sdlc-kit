# SDLC cheatsheet

Use this during a run. `AGENTS.md` holds the full rules; the `sdlc` skill drives the stages.

## Pipeline

| # | Stage | Output | Gate |
| --- | ------- | -------- | ------ |
| 0 | Context + Foundation | context, configured test strategy, product PRD, foundational ADRs, architecture/security, core contract | bootstrap: context filled, then approve foundation; adopt: approve reconstructed foundation |
| 1 | Spec | optional brief, hardened PRD; no issues yet | approve PRD |
| 2 | Architecture + Contract | ADRs, architecture/security updates, frozen contract | approve and freeze |
| 3 | Decompose | tracker issues | disclose |
| 4 | Implement | one task on a `feat/*` branch | approve compact in-session task plan |
| 5 | QA | tests, runtime observation or relevant non-runtime check, CI | - |
| 6 | Review | clean diff; security review when required | inline |
| 7 | Land | PR if supported; otherwise push if a remote exists, run available CI, and merge directly. **GitHub:** `Closes #N`. **Other trackers/local-only:** no keyword; complete after merge | **human merges** |
| 8 | Retro | per-task learnings; final-child artifact and epic reconciliation | - |

Fresh projects have six hard gates: context, foundation, PRD, architecture and contract, each task
plan, and merge. Existing-project adoption combines Stage 0 into one approval, so it has five. Stop
for a human “yes” at each gate. At other stages, do the work, disclose decisions, and continue.
Repository-action approval is a safety stop, not an extra pipeline gate. One combined approval may
cover commit, push, and PR creation when the request names all three; merge always stays separate.

## Choose the path

- **Feature, user-facing, or risky:** Stages 1–8 after one-time Stage 0 bootstrap/adoption.
- **Bug fix or small enhancement:** Implement → QA → Review → Land → Retro.
- **Chore, docs, or dependency update:** Implement → Review → Land → Retro.
- Use the full pipeline when a change affects a contract, sensitive area, or decision.

## Core rules

- **Foundation versus feature:** establish only the project-wide PRD, ADRs, architecture, threat
  model, and core contract at Stage 0. Let feature artifacts emerge per feature.
- **Contract first:** define and freeze the interface before implementation. Generate shared types.
  Changing a shipped contract requires a versioning or deprecation ADR.
- **Sensitive areas:** use the canonical list in [`AGENTS.md`](./AGENTS.md#sensitive-areas).
  Threat-model sensitive planning in `docs/security.md` and run `security-review` before landing it;
  review the implementation again at Stage 6.
- **Ask instead of guessing:** stop on ambiguous PRDs, ADRs, and contracts.

## Ready and done

**Ready:** testable acceptance criteria, frozen contract, no open questions, and about one day of
work.

**Done:** acceptance criteria met; contract honored; expand/contract used once real data or deployed
readers/writers exist; proportional verification complete; available CI green; reviews clean;
architecture, ADRs, and tracker current. Unreachable CI blocks. Tracker closure happens after merge.

## Git

- Keep `main` deployable. Use short-lived `feat/{id}-{slug}` branches.
- Use `type(scope): summary` Conventional Commits, imperative and at most 72 characters.
- Reference GitHub issues with `Refs #N` or `Closes #N`; use native keys for other trackers and no
  issue syntax for local-only IDs.
- Commit the Stage 1–2 planning package to `main` once after Stage 2, before branching. Stage 0
  foundation artifacts may be committed after their gate. If `main` is protected, merge a `plan/*`
  PR first.
- Keep commits and PRs focused. The human always merges.

## Artifact map

| Artifact | Location |
| ---------- | ---------- |
| Domain and durable learnings | `docs/context.md` |
| Product and feature PRDs | `docs/prd/` |
| Decisions | `docs/adr/` |
| Current system shape | `docs/architecture.md` |
| Integration truth | contract source named in `docs/contracts/README.md` |
| Threat model | `docs/security.md` |
| Test policy | `docs/test-strategy.md` |
| Task status | external tracker, or `docs/progress.md` in local-only mode |

After all descendant tasks under an epic-level group are done, optionally run `improve` for a scoped
audit. Do not suggest it after each leaf task or small parent task. At epic completion, `improve
next` can surface future directions; after choosing one, decline its planning step and start
`sdlc {chosen direction}`. `improve` is code-read-only but writes `plans/`; it stays outside the
pipeline and never replaces Stage 1.

For comments on an open PR, run `address-review`. It triages human and bot feedback before fixing,
refuting, or deferring each comment.
