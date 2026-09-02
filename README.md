# sdlc

A portable, plan-gated workflow for building software with AI agents.

The kit combines a conductor skill, an `AGENTS.md` operating manual, and project templates. The
conductor routes work through nine stages. A one-task feature has six human approval gates for a
fresh project or five after adoption; each additional task repeats its plan and merge gates. It
targets web, API, SaaS, and API-backed cross-platform mobile apps by default, but its plain
Markdown skills can run in any agent that supports `SKILL.md` files.

> This is a workflow kit, not one standalone skill. Its installer adds every stage-bound skill file
> to the target project before you invoke `sdlc`.

## Fit

The defaults assume a web-shaped product: contracts, CI, database migrations, and deployable
branches. Backend services, CLIs, libraries, and cross-platform apps can replace the UI test and
deployment tools.

The workflow uses Architecture Decision Records, C4-style architecture documentation,
contract-first development, GitHub Flow, and phase gates. Pinned third-party skills remain
unchanged. The installer adds local provenance and
license metadata; source pins live in [`vendor/skills.lock.json`](./vendor/skills.lock.json), and
upstream terms live in [`vendor/licenses/`](./vendor/licenses/).

## Core model

Artifacts have two levels:

- **Foundation:** project-wide context, configured test strategy, product PRD, foundational ADRs,
  architecture, security threat model, and core contract. Create these once at Stage 0.
- **Feature:** a brief, feature PRD, feature ADRs, and contract slice. Create these as each feature
  moves through Stages 1–8.

Artifacts also have two homes:

- **Repository:** durable reasoning in `docs/`.
- **Tracker:** live tasks and status. GitHub Issues is the default; Linear and Jira require a small
  port. Without an external tracker, `docs/progress.md` becomes the tracker.

## Pipeline

| # | Stage | Output | Gate |
| --- | ------- | -------- | ------ |
| 0 | Context + Foundation | context, test strategy, product PRD, foundational ADRs, architecture/security, core contract | bootstrap: context filled, then approve foundation; adopt: approve reconstructed foundation |
| 1 | Spec | optional brief, hardened feature PRD | approve PRD |
| 2 | Architecture + Contract | ADRs, architecture/security updates, frozen contract | approve and freeze |
| 3 | Decompose | tracker issues | disclose |
| 4 | Implement | code on a `feat/*` branch | approve each compact in-session task plan |
| 5 | QA | tests, runtime observation or relevant non-runtime check, CI | - |
| 6 | Review | clean diff; security review when required | inline |
| 7 | Land | PR when supported; otherwise push if a remote exists, run available CI, and merge directly | human merges |
| 8 | Retro | per-task learnings; final-child artifact and epic reconciliation | - |

Before landing a Stage 0 or Stage 2 planning package that touches a sensitive area, update
`docs/security.md` and run `security-review`; review the implementation diff again at Stage 6.

At Land, GitHub PRs use `Closes #N`; the issue closes on merge. Other trackers use their native
integration or a post-merge transition. Local-only projects update `docs/progress.md`. If hosting
has no PR workflow, push when a remote exists, run available CI, and let the human merge directly.

### Right-size the process

| Change | Path |
| -------- | ------ |
| Feature, user-facing change, or risky work | Stages 1–8 after one-time Stage 0 bootstrap/adoption |
| Bug fix or small enhancement | Implement → QA → Review → Land → Retro |
| Chore, documentation, or dependency update | Implement → Review → Land → Retro |

A change enters the full pipeline when it changes a contract, touches a sensitive area, or records
a decision.

## Quick start

Check the required [installation prerequisites](./INSTALL.md#prerequisites), including the POSIX
filesystem operations used for safe publication. Then clone this repository once and run its
non-destructive installer against your project:

```bash
./install.sh /path/to/your/project

# Preview without writing
./install.sh --dry-run /path/to/your/project

# Use a runtime-specific skills directory
SKILLS_DIR=/path/to/your/project/.claude/skills \
  ./install.sh /path/to/your/project
```

All stage-bound skills install to `{project}/.agents/skills` by default. Existing skill directories
are never overwritten or merged.

Next:

1. Ask your agent to start `sdlc`.
2. Complete Stage 0 before starting a feature.

For a worked run, read [`EXAMPLE.md`](./EXAMPLE.md). Keep [`CHEATSHEET.md`](./CHEATSHEET.md) nearby
once the workflow is familiar.

## Existing projects

Run the same installer. It adds missing files but leaves existing ones untouched. Merge the kit's
`AGENTS.md` and `docs/` sections into your versions instead of replacing them. Move durable runtime
instructions into `AGENTS.md`, then keep `CLAUDE.md` as a one-line pointer when that runtime supports
it. The conductor's `adopt` path reconstructs context and architecture without changing behavior.

## Portability

- `AGENTS.md` is canonical. Runtime-specific files such as `CLAUDE.md` should point to it.
- Agent replies default to compact, outcome-first prose. Apply the bundled `unslop` adaptation
  automatically to human-facing replies and prose where applicable; follow its canonical scope and
  exclusions.
- Skills are portable Markdown. Each stage has a manual fallback in `required-skills.yml`.
- Stage-bound third-party skills are pinned under `vendor/skills/` and installed project-locally.
  Optional companions remain separate.
- `required-skills.yml` is the kit's supported-skill manifest: pipeline dependencies, standalone
  utilities, optional companions, and their fallbacks. You can install other skills; they do not
  become pipeline stages unless you update the workflow and conductor.
- GitHub is the default tracker and PR host, not a runtime requirement.
- Stack, branch names, test tools, deployment targets, Definition of Done, and gates are defaults.
  Adapt policy in `AGENTS.md` and project docs. For branch or gate changes, also update the installed
  conductor, `feature-start`, affected summaries, and validation checks so execution follows policy.

## Repository map

| Path | Purpose |
| ------ | --------- |
| `AGENTS.md` | configured maintainer-repository workflow rules |
| `templates/AGENTS.md` | project workflow template installed with a Stage 0 stack sentinel |
| `templates/CLAUDE.md` | one-line pointer to the installed operating manual |
| `docs/context.md` | source-repository context for maintainers and coding agents |
| `install.sh` | merge-aware installer with `--dry-run` |
| `skills/` | conductor, kit-owned workflow skills, and standalone utilities |
| `vendor/skills/` | pinned, unmodified third-party pipeline skills |
| `vendor/skills.lock.json` | upstream revisions, paths, content hashes, and license hashes |
| `scripts/vendor-skills.py` | verifies, restores, and refreshes vendored snapshots |
| `templates/docs/` | context, PRD, ADR, architecture, security, contract, test, and runbook templates |
| `templates/github/` | CI, issue, and pull-request templates |
| `required-skills.yml` | supported-skill manifest and manual fallbacks |
| `scripts/validate-kit.sh` | maintainer validation and install smoke test |

The optional code-read-only `improve` skill can audit a completed epic-level group and write fix
plans under `plans/` after all descendant tasks are done. It is not suggested after each leaf task
or small parent task. It can also
suggest future directions after that epic-level group. It sits outside the pipeline; see
[`INSTALL.md`](./INSTALL.md#additional-skills).
