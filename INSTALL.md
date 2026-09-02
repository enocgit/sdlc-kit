# Install

## Prerequisites

The installer requires:

- A POSIX environment with Bash and Python 3.10+.
- Filesystems that support descriptor-relative operations, same-directory hard links, and
  `renameat2` or `renameatx_np`. `install.sh --dry-run` checks the OS. A real install also checks
  each target filesystem before writing.
- Git 2.25 or newer. Before the first review, run `git rev-parse --show-object-format` in the target
  repository. Upgrade Git if this fails.
- An agent that loads `SKILL.md` files and can run shell commands.
- GitHub CLI when the project uses GitHub issues or pull requests. Run `gh auth login` with `repo`
  scope. Add `project` scope only for GitHub Projects:

  ```bash
  gh auth refresh -s project
  ```

A project with a remote must support non-interactive `git push`. For a GitHub SSH remote, load the
key and test it:

```bash
ssh-add -l
ssh -T git@github.com
```

GitHub may return status 1 after successful authentication because it does not provide shell access.
To use HTTPS instead, configure GitHub CLI and change the remote explicitly:

```bash
gh auth login
gh auth setup-git
git remote set-url origin https://github.com/OWNER/REPOSITORY.git
```

Do not add a broad Git URL rewrite. Projects without a remote need no push credentials or PR host.
An unreachable configured remote still blocks Land.

## 1. Install the kit

Run the installer from this repository:

```bash
./install.sh /path/to/your/project

# Preview without writing
./install.sh --dry-run /path/to/your/project
```

The installer adds missing files. It never overwrites an existing destination.

| Source | Destination |
| --- | --- |
| `templates/AGENTS.md` | `AGENTS.md` |
| `templates/CLAUDE.md` | `CLAUDE.md` |
| `required-skills.yml` | `required-skills.yml` |
| `templates/docs/` | `docs/` |
| `templates/github/` | `.github/` |
| `skills/`, `vendor/skills/` | `.agents/skills/` by default |

Set `SKILLS_DIR` if the runtime reads another project-local directory:

```bash
SKILLS_DIR=.claude/skills ./install.sh /path/to/your/project
```

A relative path resolves inside the target project. An absolute path must belong only to that
project. The installer rejects common user-global directories, including `~/.agents/skills` and
`~/.claude/skills`, so pipeline skills do not load in unrelated projects.

The installer copies directories. You may instead link `.claude/skills` to `../.agents/skills`.
Committed links may fail on Windows without developer mode, in some CI checkouts, or across Docker
bind mounts.

Each file or skill publication is atomic, so the destination is either absent or complete. The
installer gives control directories mode `0700`, skill directories `0755`, and files `0644` or
`0755` based on executable intent.

After an interruption, the next install locks the parent directory and moves marked stale state to
`.sdlc-preserved-*`. Inspect that directory before removing it. The installer does not touch an
unmarked lookalike. An interruption while writing recovery intent may also leave
`.sdlc-staging-intent.tmp-*`, which requires manual inspection and removal.

If the target tracks installer state, ignore these names:

```gitignore
.sdlc-staging-intent
.sdlc-staging-intent.tmp-*
.sdlc-file-*
.sdlc-skill-*
.sdlc-rename-probe-*
.sdlc-preserved-*
```

### Upgrade an existing installation

Re-running the installer adds new files but does not replace existing files or skills.

1. Commit or back up the target. Update this kit checkout and review its `CHANGELOG.md` and diff.
2. Stop agents that use the target.
3. Record absolute paths. Keep the skills directory project-specific:

   ```bash
   TARGET=/absolute/path/to/the/project
   SKILLS_DIR_ABS=/absolute/path/to/the/project/.agents/skills
   ```

4. Preview with those paths. Merge changes to existing root and `docs/` files by hand:

   ```bash
   SKILLS_DIR="$SKILLS_DIR_ABS" ./install.sh --dry-run "$TARGET"
   ```

5. Move each bundled skill directory to a backup outside `SKILLS_DIR_ABS`, then install:

   ```bash
   SKILLS_DIR="$SKILLS_DIR_ABS" ./install.sh "$TARGET"
   ```

6. Review the target diff and verify the installed snapshots:

   ```bash
   python3 scripts/vendor-skills.py verify-installed "$SKILLS_DIR_ABS"
   ```

7. Run the target project's validation. Delete the backup only after it passes.

If validation fails, leave agents stopped. Remove the failed replacement skills, restore the
backups, restore root and `docs/` files from the pre-upgrade commit or backup, and rerun the old
validation.

If the runtime does not read `AGENTS.md`, point its instruction file to it:

```text
See AGENTS.md for how we work on this project.
```

## 2. Review the bundled skills

The installer copies these stage-bound skills into the target project. It does not use a registry or
change user-global skills.

| Skill | Upstream | Stage |
| --- | --- | --- |
| `brainstorming` | obra/superpowers | Spec |
| `to-prd` | mattpocock/skills | Spec |
| `grilling` | mattpocock/skills | Spec |
| `documentation-and-adrs` | addyosmani/agent-skills | Foundation, Architecture |
| `writing-plans` | obra/superpowers | Decompose |
| `using-git-worktrees` | obra/superpowers | Implement |
| `frontend-design` | anthropics/skills | Implement, UI only |
| `ponytail` | DietrichGebert/ponytail | Implement, backend/domain and dependency choices |
| `webapp-testing` | anthropics/skills | QA, browser UI only |
| `improve-codebase-architecture` | mattpocock/skills | Adopt an existing project |

`vendor/skills/` contains exact upstream snapshots. The installer preserves their contents and adds
`$SKILLS_DIR/{skill}/.sdlc-vendor/` with provenance and license files. `to-prd` remains pinned to the
last reviewed revision before its rename to `to-spec`. See
[`vendor/skills.lock.json`](./vendor/skills.lock.json) for every pinned commit.

Use the runtime's available tools for runtime observation, code review, simplification, and
security review. `required-skills.yml` provides concrete manual fallbacks where available. The
bundled `unslop` adaptation applies automatically to human-facing communication where
applicable; follow its canonical scope and exclusions.

Skills run with the agent's permissions. Read each `SKILL.md`, then commit the project-local copies
so every team and CI environment uses the same instructions.

The unchanged snapshots need these precautions:

- Before using the `brainstorming` visual companion, export
  `SUPERPOWERS_DISABLE_TELEMETRY=1`. Keep it on loopback with its default temporary session
  directory. Do not pass `--project-dir`. Use an SSH tunnel for remote access. Ignore its commit and
  `docs/superpowers/` instructions because the conductor owns those actions.
- The `improve-codebase-architecture` HTML report loads unpinned Tailwind and Mermaid scripts and
  enables Mermaid loose mode. For a private or sensitive repository, use pinned local assets with
  strict mode or skip the report.
- Before `using-git-worktrees` runs setup or build commands, name the command and get approval. For
  an in-repository worktree, require `git check-ignore -q "$LOCATION/"` to pass.
- Do not use `webapp-testing`'s `with_server.py`. Use the project's lifecycle runner or an existing
  server. Wait for an app-specific locator, URL, or health check rather than `networkidle`.

Maintainers need PyYAML. Follow [CONTRIBUTING.md](./CONTRIBUTING.md) when updating snapshots. These
commands restore locked content or verify it offline:

```bash
python3 scripts/vendor-skills.py sync
python3 scripts/vendor-skills.py verify
```

`required-skills.yml` lists pipeline dependencies, standalone utilities, and optional companions.
To add a pipeline skill, update `AGENTS.md`, `required-skills.yml`, the snapshot and provenance when
applicable, and the installed conductor at `$SKILLS_DIR/sdlc/SKILL.md`.

### Additional skills

The kit does not manage skills outside `required-skills.yml`. Install any additional skill with your
runtime's normal command, either for the project or for your user account.

Teams may add `test-driven-development` when they want strict TDD for all behavior changes. The
kit's default remains the proportional policy in `docs/test-strategy.md`.

The optional `improve` skill can audit a completed epic or suggest a direction with `improve next`.
It remains outside the pipeline. Install it only where you want it available, keep its `plans/`
output temporary, and route selected directions through Stage 1 with `sdlc {chosen direction}`.

## 3. Adapt the project

### Tracker

GitHub Issues is the default. For Linear or Jira, replace these integration points without changing
the surrounding workflow:

| Responsibility | GitHub default | Replacement |
| --- | --- | --- |
| Create tasks | `gh issue create` in `$SKILLS_DIR/sdlc/SKILL.md` | Tracker API or CLI |
| Report status | `gh issue list` or `gh project item-list` | Tracker query |
| Complete tasks | `Closes #N` | Native Git integration or post-merge update |
| Name branches | Issue number | Tracker key such as `ENG-123` |

Without a Git integration, close the task after the human confirms the merge. For local-only work,
use `docs/progress.md`. Delete that file when an external tracker is authoritative.

### CI and end-to-end tests

Replace the commands in `.github/workflows/ci.yml` with the project's lint, typecheck, test, and
build commands. Existing CI must pass. An unreachable workflow blocks Land. Without pull requests,
push-triggered CI still runs before the human merges.

Use the platform's E2E runner: Playwright for web, or Maestro or Detox for mobile. A Playwright MCP
server is optional and useful only for interactive browser work.

### Custom skills

You may use `skill-creator` when creating or substantially changing the maintained skills in
`skills/`. Either way, keep each `SKILL.md` portable, validate its frontmatter, match its `name` to
its directory, and write a specific trigger description.

## 4. Smoke test

Ask the agent to start `sdlc`. A fresh installation should find `> STATUS: TEMPLATE` in
`docs/context.md`, begin Stage 0, and stop at the context gate. It must not enter Spec before Stage 0
is complete.
