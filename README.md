# sdlc

A portable, tool-agnostic, plan-gated pipeline for building quality software with AI agents.

Greenfield-first (its primary purpose) with an on-ramp for existing codebases. Every
feature flows through the same stages; each stage produces a durable artifact; the agent
stops at defined **gates** for human approval.

> **This is a workflow _kit_, not a single skill.** It's a conductor skill + doc templates + an
> operating manual (`AGENTS.md`) that together run the pipeline. The conductor orchestrates a set of
> community skills — it borrows their _technique_ while owning the _workflow_ — so expect a one-time
> setup ([INSTALL.md](./INSTALL.md)), not a drop-in `npx skills add`.

These aren't house rules — the building blocks are long-standing practice. Decisions are recorded
as [Architecture Decision Records](https://adr.github.io/) (Michael Nygard's format), the
architecture doc follows the [C4 model](https://c4model.com/) (Simon Brown), and the human approval
**gates** are a lightweight [phase-gate](https://en.wikipedia.org/wiki/Phase-gate_process) model
(Cooper's Stage-Gate). The kit's contribution is wiring proven artifacts into one agent-driven
pipeline — not reinventing them.

Built on community skills from **obra/superpowers**, **mattpocock/skills**, **anthropics/skills**,
**addyosmani/agent-skills**, and **shadcn** — installed from their sources (see
[`required-skills.yml`](./required-skills.yml)), not vendored here, so each keeps its own license.

## Scope & fit

Best fit: full-stack **web / API / SaaS** product work — the defaults are shaped for it. It adapts
cleanly to **backend services, CLIs, and libraries** (skip the UI skills), and to **cross-platform
app work like React Native / Expo** — TS + React against an API-backed contract is the kit's sweet
spot; just swap the browser-specific test tool (Playwright → Detox/Maestro) and the deploy model
(web preview/staging/prod → app-store/EAS) for your platform's. Weaker fit for **ML/data-science
research, embedded/firmware, native mobile (Swift/Kotlin), and game dev** — the contract-first
"freeze the interface," expand/contract migrations, "app runs" QA, and GitHub-Flow deploy
assumptions don't map cleanly there, so you'd be adapting the method more than following it. The
*pipeline* (stages + gates + artifacts) is portable; the *defaults* (stack, contract artifacts, CI,
deploy) are web-shaped and meant to be swapped.

## Two altitudes: foundation vs feature

A core distinction the pipeline is built around:

- **Project-level (foundation)** — set **once, early** (Stage 0): the product PRD
  (`docs/prd/0000-product.md`), cross-cutting ADRs (stack, repo layout, auth, datastore, API
  style), the architecture skeleton, and the core contract. These belong to no single feature.
- **Feature-level** — produced **per feature** (Stages 1–8): a brief, a feature PRD, feature
  ADR(s), and a contract *slice*.

Greenfield projects lock the foundation at Stage 0 (`bootstrap` → 0a Context, 0b Foundation);
existing projects reverse-engineer it (`adopt`). Either way, keep the foundation minimal — most
ADRs and contracts are feature-driven and should emerge as you build, not be guessed up front.

## Two homes for artifacts (hybrid)

- **In-repo `docs/`** — the durable *why*: PRDs, ADRs, architecture, contracts, test strategy.
  Versioned, diffable, survives tool changes.
- **GitHub Issues / Projects (default)** — the live *what's happening*: epics, tasks, progress.

The tracker is the single source of truth — there is **no in-repo mirror to sync**; the
`project-status` skill reports status live from it (read-only). The kit is **GitHub-first,
tracker-adaptable** — a small manual port, not a config toggle: `project-status` assumes `gh`, but
you can retarget it to Linear/Jira by swapping the tracker commands in three skills — a well-scoped
job you can hand the agent to port cleanly (see [INSTALL.md §4](./INSTALL.md#4-tool-specific-nuances)),
or run "local-only" with `docs/progress.md` as the tracker itself (the one mode where that file is used).

## The pipeline

| # | Stage | Output | Skill | Gate |
|---|-------|--------|-------|------|
| 0 | On-ramp — **0a Context** + **0b Foundation** (`bootstrap` new / `adopt` existing) | filled `docs/context.md`; product PRD (`prd/0000-product.md`), foundational ADRs, architecture skeleton, core contract | templates / `documentation-and-adrs` / `improve-codebase-architecture` | ✅ approve foundation |
| 1 | Spec (discovery → PRD → stress-test) | brief `docs/briefs/*` → hardened PRD `docs/prd/*` (no issues yet) | `brainstorming` → `to-prd` → `grill-me` | ✅ approve PRD |
| 2 | Architecture + Contract | ADR(s), `docs/architecture.md`, `docs/security.md`, **frozen** `openapi.yaml`/tRPC/schema | `documentation-and-adrs` | ✅ approve + freeze |
| 3 | Decompose | **tracker issues** (GitHub by default) — the tracker is the record | `writing-plans` + `project-status` | disclose |
| 4 | Implement | code on a `feat/*` branch | `feature-start`, `executing-plans` (`frontend-design` for UI work) | ✅ per task |
| 5 | QA | tests green, app runs, CI green | `test-driven-development`, `run` / `verify` (`webapp-testing` for UI) | — |
| 6 | Review | clean diff (`security-review` if sensitive) | `code-review`, `simplify`, `definition-of-done-review` | inline |
| 7 | Land & track | PR opened; tracker updated (issue closed) | `project-status` | ✅ human merges |
| 8 | Retro | `context.md` Learnings (+ optional agent memory) | reflect + write (native) | — |

### Right-size the process (don't run all 9 stages for a typo)

Forcing the full pipeline on a one-line fix kills adoption. Match ceremony to change size:

| Change type | Path |
|-------------|------|
| **Feature / anything user-facing or risky** | Full pipeline (0→8) |
| **Bug fix / small enhancement** | Skip to **4 Implement → 5 QA → 6 Review** (reference an issue; no PRD/contract/ADR unless a decision or contract changes) |
| **Chore / docs / dep bump** | **4 → 6** with a trivial diff; CI must still be green |

Rule: the moment a "small" change touches a **contract**, a **security-sensitive area**, or makes a **decision**, it graduates to the full path. When in doubt, ask.

### Beyond the pipeline (optional but highly recommended companion)

The pipeline manages two altitudes (foundation, feature); a third sits *outside* it. After an epic
closes, the optional **`improve`** companion — a read-only advisor, **not a stage and not gated** —
surveys what you built at the portfolio/roadmap altitude: its **audit** writes fix plans
(bugs/debt/perf/tests) to `plans/`, while **`improve next`** surfaces candidate directions you hand
back into **Stage 1**. It composes with `docs/` but is never required, and it never edits code,
merges, or pushes. Setup and usage discipline in [INSTALL.md](./INSTALL.md) (§2, *Highly Recommended
companion skill*).

## How to use

This kit is a **source template**, not a dependency you install into your app. Clone it once,
then copy the relevant pieces into *your* project. You do **not** copy the kit's own meta files
(`README`, `LICENSE`, `CONTRIBUTING`, `CHANGELOG`).

**Option A — one command.** Run the installer (non-destructive, never overwrites existing files).
It self-locates the kit and takes the target as an argument, so either invocation works:

```bash
# from the kit, pointing at your project:
./install.sh /path/to/your/project

# or from inside your project (target defaults to the current directory):
/path/to/sdlc/install.sh

# preview without writing:        ./install.sh --dry-run /path/to/your/project
# skills go to {project}/.claude/skills by default; override with:
# SKILLS_DIR=/path/to/your/project/.agent/skills ./install.sh /path/to/your/project
```

**Option B — manual.** Copy into your project:

| From (in this kit) | To (your project) |
|--------------------|-------------------|
| `AGENTS.md` | project root (+ a one-line `CLAUDE.md` pointer) |
| `required-skills.yml` | project root (the conductor's fallbacks read it) |
| `templates/docs/` | `docs/` |
| `templates/ci.yml` | `.github/workflows/ci.yml` |
| `templates/github/` | `.github/` (PR + epic/task issue templates) |
| `skills/` | your agent's skills dir (`.claude/skills/`, `.agent/skills/`, …) |

Then install the community skills ([`INSTALL.md`](./INSTALL.md)) and invoke the **conductor**:
ask the agent to "start the sdlc" (or `/sdlc`). It reads `AGENTS.md`, figures out the current
stage, and routes you to the right skill — stopping at every gate.

See [`EXAMPLE.md`](./EXAMPLE.md) for a full walkthrough on both a new and an existing project.

## Adopting into a repo that already has files

This kit assumes a clean drop-in. If your project **already has** `AGENTS.md`, `CLAUDE.md`, or a
`docs/` folder, **do not overwrite them** — merge:

- Treat the templates as a *checklist of sections to add*, not a replacement.
- Back up or section-merge existing content; preserve your team's prior decisions and history.
- For `CLAUDE.md`/`.cursorrules`: if they already hold rules, add the one-line pointer to
  `AGENTS.md` alongside them rather than replacing.

The conductor skill is instructed to detect existing files and surface conflicts instead of
clobbering, but review the merge yourself.

## These are defaults — adapt them to your team

Conventions in `AGENTS.md`, `docs/test-strategy.md`, and `docs/runbook.md` are starting points,
not law. Expect to tune, for example:

- **Branch & env naming** (`feat/…`, `main`/`staging`/`release`) to match your Git flow.
- **Stack** (the TS/React + Node assumptions) to your actual stack.
- **Test layers / tools** (Vitest, Playwright) to what you use.
- **Definition of Done** and the gate set to your team's risk tolerance.

Keep `AGENTS.md` as the single source of truth and update it when conventions change. Note this
is *guidance*, not a runtime guarantee: real enforcement comes from agent adherence **plus CI and
the review gates/checklists** — `AGENTS.md` existing doesn't enforce anything on its own.

See [`INSTALL.md`](./INSTALL.md) §4 for tool-specific nuances (skills directory, `gh`,
Playwright/MCP).

## Why tool-agnostic

- `AGENTS.md` is the canonical operating manual (cross-tool standard). `CLAUDE.md`,
  `.cursorrules`, etc. are one-line pointers to it — no duplication.
- Skills are portable `SKILL.md` files (frontmatter + markdown). Nothing here is bound to a
  specific agent runtime.
- The pipeline is plain markdown + git. Agent-specific accelerators are optional; each stage has
  a manual fallback (see `required-skills.yml`).
- **Scope of the claim:** "tool-agnostic" is about the *agent runtime* (any agent can follow
  `AGENTS.md` + the portable `SKILL.md` files). The *tracker* is GitHub-first but swappable, and
  the one Claude-specific piece — `skill-creator` — is an **optional authoring aid for maintaining
  the custom skills, never needed to run the pipeline** on any runtime.

## Folder map

```
sdlc/
├── README.md                 ← this file
├── install.sh                ← copies the kit into a target project (merge-aware, --dry-run)
├── AGENTS.md                 ← operating-manual template (copy to project root)
├── INSTALL.md                ← community skills to install + skill-creator
├── EXAMPLE.md                ← new-project + existing-project walkthroughs
├── required-skills.yml       ← machine-readable skill manifest (kind/source/stage/fallback)
├── LICENSE                   ← MIT (open-source)
├── CONTRIBUTING.md           ← how to contribute
├── CHANGELOG.md              ← Keep a Changelog format
├── CHEATSHEET.md             ← one-page pipeline quick reference
├── .gitignore
├── scripts/
│   ├── validate-kit.sh       ← maintainer/CI checks for this kit
│   └── kit-manifest.txt      ← shipped-file inventory; validate-kit.sh diffs the tree against it
├── skills/
│   ├── sdlc/                 ← the conductor (routing + gates)
│   ├── feature-start/        ← custom: open feature branch (worktree if isolation needed) + load context, enter plan mode
│   ├── project-status/       ← custom: read-only status report from the tracker
│   ├── definition-of-done-review/  ← custom: team DoD reviewer
│   └── address-review/       ← custom: triage + address external PR review comments (standalone)
└── templates/                ← everything you copy into a project
    ├── ci.yml                ← → .github/workflows/ci.yml (enforces mechanical DoD)
    ├── github/               ← → .github/ (PR + issue templates aligned to the pipeline)
    │   ├── pull_request_template.md
    │   └── ISSUE_TEMPLATE/{epic,task}.md
    └── docs/                 ← → docs/
        ├── context.md
        ├── architecture.md
        ├── security.md       ← threat model + security checklist
        ├── briefs/TEMPLATE.md
        ├── prd/0000-product.md
        ├── prd/TEMPLATE.md
        ├── adr/0001-record-architecture-decisions.md
        ├── adr/TEMPLATE.md
        ├── contracts/README.md
        ├── progress.md          ← local-only tracker (delete if you use GitHub/Linear/Jira)
        ├── test-strategy.md
        └── runbook.md
```
