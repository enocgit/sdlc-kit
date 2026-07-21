# SDLC cheatsheet

Use this during a run. `AGENTS.md` holds the full rules; the `sdlc` skill drives the stages.

## Pipeline

| # | Stage | Output | Gate |
|---|-------|--------|------|
| 0 | Context + Foundation | context, product PRD, foundational ADRs, architecture, core contract | bootstrap: context filled, then approve foundation; adopt: approve reconstructed foundation |
| 1 | Spec | optional brief, hardened PRD; no issues yet | approve PRD |
| 2 | Architecture + Contract | ADRs, architecture/security updates, frozen contract | approve and freeze |
| 3 | Decompose | tracker issues | disclose |
| 4 | Implement | one task on a `feat/*` branch | approve task plan |
| 5 | QA | tests, running app, CI | - |
| 6 | Review | clean diff; security review when required | inline |
| 7 | Land | PR if supported; otherwise push if a remote exists, run available CI, and merge directly. **GitHub:** `Closes #N`. **Other trackers/local-only:** no keyword; complete after merge | **human merges** |
| 8 | Retro | up to three durable context learnings | - |

Fresh projects have six hard gates: context, foundation, PRD, architecture and contract, each task
plan, and merge. Existing-project adoption combines Stage 0 into one approval, so it has five. Stop
for a human “yes” at each gate. At other stages, do the work, disclose decisions, and continue.

## Choose the path

- **Feature, user-facing, or risky:** full pipeline, 0–8.
- **Bug fix or small enhancement:** Implement → QA → Review.
- **Chore, docs, or dependency update:** Implement → Review.
- Use the full pipeline when a change affects a contract, sensitive area, or decision.

## Core rules

- **Foundation versus feature:** establish only the project-wide PRD, ADRs, architecture, and core
  contract at Stage 0. Let feature artifacts emerge per feature.
- **Contract first:** define and freeze the interface before implementation. Generate shared types.
  Changing a shipped contract requires a versioning or deprecation ADR.
- **Sensitive areas:** authentication, authorization, payments, PII/KYC, uploads, and privileged
  surfaces require a Stage 2 threat model and Stage 6 `security-review`.
- **Ask instead of guessing:** stop on ambiguous PRDs, ADRs, and contracts.

## Ready and done

**Ready:** testable acceptance criteria, frozen contract, no open questions, and about one day of
work.

**Done:** acceptance criteria met; contract honored; expand/contract used once real data or deployed
readers/writers exist; tests and app verified; available CI green; reviews clean; focused diff;
architecture, ADRs, and tracker current. Unreachable CI blocks. Tracker closure happens after merge.

## Git

- Keep `main` deployable. Use short-lived `feat/{id}-{slug}` or `fix/*` branches.
- Use `type(scope): summary` Conventional Commits, imperative and at most 72 characters.
- Reference GitHub issues with `Refs #N` or `Closes #N`; use native keys for other trackers and no
  issue syntax for local-only IDs.
- Commit approved Stage 0–2 artifacts to `main` before branching. If `main` is protected, merge a
  `plan/*` PR first.
- Keep commits and PRs focused. The human always merges.

## Artifact map

| Artifact | Location |
|----------|----------|
| Domain and durable learnings | `docs/context.md` |
| Product and feature PRDs | `docs/prd/` |
| Decisions | `docs/adr/` |
| Current system shape | `docs/architecture.md` |
| Integration truth | contract source named in `docs/contracts/README.md` |
| Threat model | `docs/security.md` |
| Test policy | `docs/test-strategy.md` |
| Task status | external tracker, or `docs/progress.md` in local-only mode |

After an epic, optionally run `improve` for an audit or `improve next` for future directions. After
choosing a direction, decline its planning step and start `sdlc {chosen direction}`. `improve` is
read-only, outside the pipeline, and never replaces Stage 1.

For comments on an open PR, run `address-review`. It triages human and bot feedback before fixing,
refuting, or deferring each comment.
