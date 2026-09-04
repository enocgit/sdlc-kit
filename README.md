# sdlc

`sdlc` is a project-local workflow kit for building software with AI agents. It gives an agent a
repeatable way to plan, implement, verify, review, and land changes while recording the decisions
in the project.

The kit installs:

- a conductor skill that routes work through the workflow;
- a project operating manual from `templates/AGENTS.md`, installed as `AGENTS.md`;
- templates for product, architecture, security, contract, test, runbook, and progress docs; and
- pinned stage skills that stay in the project instead of a user's global skill directory.

It works with web and API products, SaaS, backends, CLIs, libraries, and cross-platform mobile
apps. The defaults assume contracts, continuous integration (CI), database migrations, and
deployable branches. Projects can replace the UI, deployment, and test tools with their own.

## Start here

### 1. Check prerequisites

Read the [installation prerequisites](./INSTALL.md#prerequisites).

### 2. Install the kit

Clone this repository once, then enter its directory:

```bash
git clone https://github.com/enocgit/sdlc-kit.git
cd sdlc-kit
```

From that checkout, run:

```bash
./install.sh /path/to/your/project

# Preview without writing
./install.sh --dry-run /path/to/your/project

# Use a runtime-specific skills directory
SKILLS_DIR=/path/to/your/project/.claude/skills \
  ./install.sh /path/to/your/project
```

### 3. Prepare and start the workflow

Before starting `sdlc`, follow the [adaptation guidance](./INSTALL.md#3-adapt-the-project) if the
project differs from the defaults.

Then ask your agent to start `sdlc`.

The installer adds missing files, never overwrites existing destinations, and writes only to the
target project and any explicitly selected project-specific `SKILLS_DIR`. For a worked example,
read [`EXAMPLE.md`](./EXAMPLE.md). Once the workflow is familiar, keep
[`CHEATSHEET.md`](./CHEATSHEET.md) nearby. Maintainers should read
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

## How the workflow works

Stage 0 establishes the project foundation once: context, test strategy, product requirements
document (PRD), architecture, security, and the core contract. Each feature then gets its own
optional brief, PRD, decisions, and contract slice. Durable documents live in `docs/`. GitHub Issues
holds live tasks and status by default. Projects can use Linear or Jira; see the [tracker integration
instructions](./INSTALL.md#tracker). Local-only projects use `docs/progress.md`.

| # | Stage | Main output | Gate or handling |
| --- | --- | --- | --- |
| 0 | Context + Foundation | filled context, product requirements document (PRD), test strategy, foundational ADRs, architecture/security, and core contract | fill context, then approve the foundation |
| 1 | Spec | optional brief and feature PRD | approve the PRD |
| 2 | Architecture + Contract | ADRs, architecture/security updates, and frozen contract | approve and freeze the contract |
| 3 | Decompose | tracker tasks | disclose the breakdown |
| 4 | Implement | code on a `feat/*` branch | approve each task plan |
| 5 | Quality assurance (QA) | tests, runtime or relevant non-runtime evidence, and CI | none |
| 6 | Review | clean diff and, when required, security review | inline; no separate gate |
| 7 | Land | pull request (PR) when supported, otherwise direct merge path | human merges |
| 8 | Retro | per-task learnings; after all feature tasks, reconcile feature artifacts, frozen contract, contract index, and parent-epic status | none |

The feature's parent tracker record, often called an epic, groups its child tasks. The workflow pauses
for human approval at the foundation, specification, architecture and contract, task-plan, and merge
points. Repository actions and external-tracker writes require separate approval; one approval may
cover commit, push, and PR creation when the request names all three. Merge always stays separate.

At Land, if hosting has no PR workflow, the agent pushes when a remote exists and runs available CI;
the human merges directly. With no remote, the human merges the local branch.

For a Stage 0 or Stage 2 planning package that touches a sensitive area, the agent updates
`docs/security.md` and runs `security-review` before asking for the human's approval to land it. Stage
6 reviews the implementation separately.

## How the agent right-sizes work

The agent selects the shortest safe path based on the change.

| Change | Path |
| --- | --- |
| Feature, user-facing change, or risky work | Stages 1–8 after Stage 0 |
| Bug fix or small enhancement | Implement → QA → Review → Land → Retro |
| Chore, documentation, or dependency update | Implement → Review → Land → Retro |

Use the full path whenever the change affects a contract, sensitive area, or recorded decision.

## Existing projects

Run the same installer. It adds missing files and leaves existing files untouched. Merge
`templates/AGENTS.md` into the project's `AGENTS.md`, and merge `templates/docs/` into the project's
`docs/` files instead of replacing them. Move runtime instructions into `AGENTS.md`; when supported,
keep `CLAUDE.md` as a one-line pointer.

The `adopt` path reconstructs the project foundation from existing code without changing its
behavior. After foundation approval, the next feature follows the normal workflow.

## Defaults and portability

- `AGENTS.md` is canonical. Runtime-specific files such as `CLAUDE.md` should point to it.
- The bundled `unslop` adaptation automatically applies to human-facing replies and prose. It leaves
  code, identifiers, schemas, contracts, commands, logs, quoted text, machine-readable output, fixed
  formats, vendor snapshots, and neutral technical records unchanged.
- Skills are portable Markdown. Each stage has a manual fallback in `required-skills.yml`.
- Stage-bound third-party skills are pinned under `vendor/skills/` and installed project-locally.
- `required-skills.yml` records pipeline dependencies, standalone utilities, and their fallbacks.
  Adding another skill does not make it a pipeline stage.
- GitHub is the default tracker and PR host, not a runtime requirement.
- Stack, branch names, test tools, deployment targets, Definition of Done, and gates are defaults.
  If a project changes them, update `AGENTS.md`, project docs, the installed conductor, affected
  skills, and validation checks together.

The installer records provenance and license metadata for vendored skills. Source pins live in
[`vendor/skills.lock.json`](./vendor/skills.lock.json), and upstream terms live in
[`vendor/licenses/`](./vendor/licenses/). Vendored snapshots remain unchanged.

## Repository map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | maintainer-repository workflow rules |
| `templates/AGENTS.md` | operating-manual template installed in projects |
| `templates/CLAUDE.md` | one-line pointer to the operating manual |
| `docs/context.md` | repository context for maintainers and agents |
| `install.sh` | merge-aware installer with `--dry-run` |
| `skills/` | conductor, kit-owned workflow skills, and utilities |
| `vendor/skills/` | pinned, unmodified third-party pipeline skills |
| `vendor/skills.lock.json` | upstream revisions, paths, content hashes, and license hashes |
| `scripts/vendor-skills.py` | verifies, restores, refreshes, and removes vendored snapshots |
| `templates/docs/` | project documentation templates |
| `templates/github/` | CI, issue, and pull-request templates |
| `required-skills.yml` | supported-skill manifest and fallbacks |
| `scripts/validate-kit.sh` | maintainer validation and install smoke test |

The optional `improve` skill reads code but does not edit it. It can write plans under `plans/` when
it audits a completed epic. Offer it only after all tasks in the epic are complete, not after a single
task. For `improve next`, decline its planning step and start `sdlc {chosen direction}` at Stage 1. Read
[`INSTALL.md`](./INSTALL.md#additional-skills) before adding it.
