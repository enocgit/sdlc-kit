# Install the workflow

## Prerequisites

- **Git** for branches and commits.
- **An agent that loads `SKILL.md` files** and can run shell commands.
- **GitHub CLI (`gh`)** when GitHub provides issues or pull requests. Run `gh auth login` with
  `repo` scope. Add `project` scope only for GitHub Projects:

  ```bash
  gh auth refresh -s project
  ```

- **For projects with a remote, `git push` must work non-interactively.** For GitHub over HTTPS,
  run:

  ```bash
  gh auth setup-git
  ```

  For an SSH remote, use a working SSH agent or configure a project-local HTTPS rewrite:

  ```bash
  git config --local url."https://github.com/".insteadOf "git@github.com:"
  ```

Projects with no remote need neither push authentication nor a PR host; the human merges the local
feature branch directly. A configured remote workflow that is unreachable remains a blocker.

## 1. Install the kit

Run the merge-aware installer from this repository:

```bash
./install.sh /path/to/your/project

# Preview without writing
./install.sh --dry-run /path/to/your/project
```

The installer adds missing files and never overwrites existing ones:

| Source | Destination |
|--------|-------------|
| `AGENTS.md` | project root |
| `required-skills.yml` | project root |
| `templates/docs/` | `docs/` |
| `templates/ci.yml` | `.github/workflows/ci.yml` |
| `templates/github/` | `.github/` |
| `skills/` | `.agents/skills/` by default |

Set `SKILLS_DIR` when your runtime uses another location:

```bash
SKILLS_DIR=.claude/skills ./install.sh /path/to/your/project
```

Relative overrides resolve inside the target project. The installer copies real directories. You
may instead symlink `.claude/skills` to `../.agents/skills`, but committed symlinks can fail on
Windows without developer mode, in some CI checkouts, or across Docker bind mounts.

If your runtime does not read `AGENTS.md`, point its instruction file to it:

```text
See AGENTS.md for how we work on this project.
```

## 2. Install community skills

The kit maintains only its conductor and workflow-specific skills. Install the remaining skills
from their sources; [`required-skills.yml`](./required-skills.yml) is the machine-readable list and
includes a manual fallback for each one.

| Skill | Source | Stage |
|-------|--------|-------|
| `brainstorming` | obra/superpowers | Spec |
| `to-prd` | mattpocock/skills | Spec |
| `grill-me` | mattpocock/skills | Spec |
| `documentation-and-adrs` | addyosmani/agent-skills | Foundation, Architecture |
| `writing-plans` | obra/superpowers | Decompose |
| `using-git-worktrees` | obra/superpowers | Implement |
| `executing-plans` | obra/superpowers | Implement |
| `frontend-design` | anthropics/skills | Implement, UI only |
| `test-driven-development` | obra/superpowers | QA |
| `webapp-testing` | anthropics/skills | QA, browser UI only; use a platform runner for mobile |
| `run`, `verify` | runtime-native or equivalent | QA |
| `code-review`, `simplify`, `security-review` | runtime-native or equivalent | Review |
| `improve-codebase-architecture` | mattpocock/skills | Adopt existing project |

Install only the **community** rows with `npx skills add`. Confirm current package names on
[skills.sh](https://skills.sh), for example:

```bash
npx skills add obra/superpowers --skill writing-plans
npx skills add addyosmani/agent-skills --skill documentation-and-adrs
```

For **runtime-native** rows, use your agent's equivalent or the documented fallback in
`required-skills.yml`; do not search for them as registry packages.

Read each `SKILL.md` before adopting it. Skills run with your agent's permissions. Prefer pinned,
reviewed versions, and commit project-scoped copies for reproducible team and CI environments.
Registry installs are snapshots: update them deliberately, inspect the diff, and re-run validation.

### Optional post-epic audit

Install `improve` user-wide if you want a read-only advisor after an epic:

- `improve` audits shipped work and writes fix plans to `plans/`.
- `improve next` surfaces directions only. Choose one, decline its planning step, then start
  `sdlc {chosen direction}` so the feature enters Stage 1.
- Keep `plans/` ephemeral: ignore it or delete completed plans.
- Land generated plans as dependency-ordered PRs; the human still merges each one.

`improve` is not a pipeline stage and never runs automatically. Do not confuse it with
`improve-codebase-architecture`, which reconstructs foundation documents when adopting a project.

## 3. Adapt the integration points

### Tracker

GitHub Issues is the default tracker. To use Linear or Jira, replace these commands while preserving
the surrounding workflow:

| Responsibility | Default | Replacement |
|----------------|---------|-------------|
| Create tasks | `gh issue create` in `skills/sdlc/SKILL.md` | tracker create API/CLI |
| Report status | `gh issue list` / `gh project item-list` in `project-status` | tracker query |
| Complete tasks | GitHub `Closes #N` | native Git integration or post-merge transition |
| Identify branches | issue number | tracker key, such as `ENG-123` |

Without a Git integration, close the tracker task only after the human confirms the merge. For
local-only work, keep `docs/progress.md`; with an external tracker, delete it.

### CI and end-to-end tests

Adapt `.github/workflows/ci.yml` to the project's lint, typecheck, test, and build commands. Existing
CI must pass; an unreachable workflow blocks Land. Without a PR workflow, push-triggered CI still
runs before the human merges directly.

Run E2E tests through the platform runner: Playwright for web, or Maestro/Detox for mobile. A
Playwright MCP server is optional and only needed for interactive browser exploration.

### Custom skills

Optionally use `skill-creator` when creating or substantially changing the five skills in `skills/`.
Regardless of tooling, keep each `SKILL.md` portable, validate its frontmatter, match its `name` to
its directory, and give it a specific triggering description.

## 4. Smoke test

Ask the agent to start `sdlc`. A fresh install should find the `> STATUS: TEMPLATE` marker in
`docs/context.md`, begin Stage 0, and stop at the context gate. It must not enter Spec until Stage 0
is complete.
