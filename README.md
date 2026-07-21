# sdlc

A portable, plan-gated workflow for building software with AI agents.

The kit combines a conductor skill, an `AGENTS.md` operating manual, and project templates. The
conductor routes work through nine stages; fresh projects stop at six human approval gates, while
existing-project adoption stops at five. It works best for web, API, SaaS, and API-backed
cross-platform mobile apps, but its plain Markdown skills can run in any agent that supports
`SKILL.md` files.

> This is a workflow kit, not one standalone skill. Install the kit and its community skills before
> invoking `sdlc`.

## Fit

The defaults assume a web-shaped product: contracts, CI, database migrations, and deployable
branches. Backend services, CLIs, libraries, and cross-platform apps can replace the UI test and
deployment tools.

The workflow uses established practices: Architecture Decision Records, C4-style architecture
documentation, contract-first development, GitHub Flow, and phase gates. Community skills remain
in their source repositories and keep their own licenses; see
[`required-skills.yml`](./required-skills.yml).

## Core model

Artifacts have two levels:

- **Foundation:** project-wide context, product PRD, foundational ADRs, architecture, and core
  contract. Create these once at Stage 0.
- **Feature:** a brief, feature PRD, feature ADRs, and contract slice. Create these as each feature
  moves through Stages 1–8.

Artifacts also have two homes:

- **Repository:** durable reasoning in `docs/`.
- **Tracker:** live tasks and status. GitHub Issues is the default; Linear and Jira require a small
  port. Without an external tracker, `docs/progress.md` becomes the tracker.

## Pipeline

| # | Stage | Output | Gate |
|---|-------|--------|------|
| 0 | Context + Foundation | context, product PRD, foundational ADRs, architecture, core contract | bootstrap: context filled, then approve foundation; adopt: approve reconstructed foundation |
| 1 | Spec | optional brief, hardened feature PRD | approve PRD |
| 2 | Architecture + Contract | ADRs, architecture/security updates, frozen contract | approve and freeze |
| 3 | Decompose | tracker issues | disclose |
| 4 | Implement | code on a `feat/*` branch | approve each task plan |
| 5 | QA | tests, running app, CI | - |
| 6 | Review | clean diff; security review when required | inline |
| 7 | Land | PR when supported; otherwise push if a remote exists, run available CI, and merge directly | human merges |
| 8 | Retro | up to three durable learnings in `docs/context.md` | - |

At Land, GitHub PRs use `Closes #N`; the issue closes on merge. Other trackers use their native
integration or a post-merge transition. Local-only projects update `docs/progress.md`. If hosting
has no PR workflow, push when a remote exists, run available CI, and let the human merge directly.

### Right-size the process

| Change | Path |
|--------|------|
| Feature, user-facing change, or risky work | Full pipeline, 0–8 |
| Bug fix or small enhancement | Implement → QA → Review |
| Chore, documentation, or dependency update | Implement → Review |

A change enters the full pipeline when it changes a contract, touches a sensitive area, or records
a decision.

## Quick start

Clone this repository once, then run its non-destructive installer against your project:

```bash
./install.sh /path/to/your/project

# Preview without writing
./install.sh --dry-run /path/to/your/project

# Use a runtime-specific skills directory
SKILLS_DIR=/path/to/your/project/.claude/skills \
  ./install.sh /path/to/your/project
```

Skills install to `{project}/.agents/skills` by default. Existing files are never overwritten.

Next:

1. Install the community skills listed in [`INSTALL.md`](./INSTALL.md).
2. Ask your agent to start `sdlc`.
3. Complete Stage 0 before starting a feature.

For a worked run, read [`EXAMPLE.md`](./EXAMPLE.md). Keep [`CHEATSHEET.md`](./CHEATSHEET.md) nearby
once the workflow is familiar.

## Existing projects

Run the same installer. It adds missing files but leaves existing ones untouched. Merge the kit's
`AGENTS.md`, `CLAUDE.md`, and `docs/` sections into your versions instead of replacing them. The
conductor's `adopt` path reconstructs context and architecture from the code without changing
behavior.

## Portability

- `AGENTS.md` is canonical. Runtime-specific files such as `CLAUDE.md` should point to it.
- Skills are portable Markdown. Each stage has a manual fallback in `required-skills.yml`.
- GitHub is the default tracker and PR host, not a runtime requirement.
- Stack, branch names, test tools, deployment targets, Definition of Done, and gates are defaults.
  Adapt them in `AGENTS.md` and the project docs.

## Repository map

| Path | Purpose |
|------|---------|
| `AGENTS.md` | canonical workflow rules copied into projects |
| `install.sh` | merge-aware installer with `--dry-run` |
| `skills/` | conductor, local workflow skills, and standalone `address-review` |
| `templates/docs/` | context, PRD, ADR, architecture, security, contract, test, and runbook templates |
| `templates/github/` | issue and pull-request templates |
| `templates/ci.yml` | starter CI workflow |
| `required-skills.yml` | community-skill manifest and manual fallbacks |
| `scripts/validate-kit.sh` | maintainer validation and install smoke test |

The optional read-only `improve` skill can audit a completed epic or suggest future directions. It
sits outside the pipeline; see [`INSTALL.md`](./INSTALL.md#optional-post-epic-audit).
