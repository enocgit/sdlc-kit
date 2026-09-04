# Install

The installer adds the kit to one project. It never overwrites an existing destination and uses a
project-local skills directory by default. It does not use a registry.

## Prerequisites

You need:

- Bash and Python 3.10+ on a POSIX system.
- Filesystems that support descriptor-relative operations and same-directory hard links.
- Git 2.25 or newer. Before the first review, run `git rev-parse --show-object-format` in the target
  repository. Upgrade Git if that command fails.
- An agent that loads `SKILL.md` files and can run shell commands.
- GitHub CLI (`gh`) when the project uses GitHub Issues or pull requests. Run `gh auth login` with `repo`
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

## 1. Install the kit

Clone this repository once, then enter its directory:

```bash
git clone https://github.com/enocgit/sdlc-kit.git
cd sdlc-kit
```

Run the installer from that checkout:

```bash
./install.sh /path/to/your/project

# Preview without writing
./install.sh --dry-run /path/to/your/project
```

The table lists the files and directories the installer publishes.

| Source | Destination |
| --- | --- |
| `templates/AGENTS.md` | `AGENTS.md` |
| `templates/CLAUDE.md` | `CLAUDE.md` |
| `required-skills.yml` | `required-skills.yml` |
| `templates/docs/` | `docs/` |
| `templates/github/` | `.github/` |
| `skills/`, `vendor/skills/` | `.agents/skills/` by default |

Set `SKILLS_DIR` when the runtime reads another skills directory:

```bash
SKILLS_DIR=.claude/skills ./install.sh /path/to/your/project
```

Relative paths stay inside the target project. Explicit absolute paths may point outside the target,
including shared or user-global directories. A project-local path remains the recommendation for
reproducible setup.

The installer copies skills into `.agents/skills` by default. If your runtime expects
`.claude/skills`, create a symbolic link from the project root:

```bash
mkdir -p .claude
ln -s ../.agents/skills .claude/skills
```

The link points `.claude/skills` to `.agents/skills`. Committed links can fail on Windows without
developer mode, in some CI checkouts, or across Docker bind mounts.

If an install stops partway through, the next install locks the parent directory and moves marked
stale state to `.sdlc-preserved-*`. Inspect that directory before removing it. The installer ignores
unmarked lookalikes. An interruption while writing recovery intent may also leave
`.sdlc-staging-intent.tmp-*`; inspect and remove it manually.

### Upgrade an existing installation

Run steps 1–6 from the `sdlc-kit` checkout. The target paths can point to another directory.

Re-running the installer adds new files but does not replace existing files or skills.

1. Commit or back up the target. Update this kit checkout and review its `CHANGELOG.md` and diff.
2. Stop agents that use the target.
3. Record absolute paths. Use a stable skills directory for the project:

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

If the runtime does not read `AGENTS.md`, point its instruction file to it:

```text
@AGENTS.md
```

## 2. Bundled skills

Projects may use the defaults only when their tracker, CI commands, and skill setup match. Read the
rest of this section when you need to know what the installer adds or when you update a bundled skill.

The installer copies these stage-bound skills to the configured `SKILLS_DIR`. It does not use a
registry. Project-local installation remains the default recommendation.

| Skill | Upstream | Stage |
| --- | --- | --- |
| `brainstorming` | obra/superpowers | Spec |
| `to-spec` | mattpocock/skills | Spec |
| `grilling` | mattpocock/skills | Spec |
| `documentation-and-adrs` | addyosmani/agent-skills | Foundation, Architecture |
| `writing-plans` | obra/superpowers | Decompose |
| `frontend-design` | anthropics/skills | Implement, UI only |
| `ponytail` | DietrichGebert/ponytail | Implement, backend/domain and dependency choices |
| `webapp-testing` | anthropics/skills | QA, browser UI only |
| `improve-codebase-architecture` | mattpocock/skills | Adopt an existing project |

`vendor/skills/` contains exact upstream snapshots. The installer preserves them and adds
`$SKILLS_DIR/{skill}/.sdlc-vendor/` with provenance and license files. The `to-spec` snapshot is pinned
to a reviewed upstream revision. See [`vendor/skills.lock.json`](./vendor/skills.lock.json) for every
pinned commit.

Use the runtime's tools for runtime observation, code review, simplification, and security review.
`required-skills.yml` provides manual fallbacks where available. The bundled `unslop` adaptation
automatically applies to human-facing replies and prose. It leaves code, commands, contracts, logs,
and other excluded content unchanged.

Skills run with the agent's permissions. Keep the project-local copies committed so every team and
CI environment uses the same instructions.

`required-skills.yml` lists pipeline dependencies and standalone utilities, with manual fallbacks.
To add a pipeline skill, update `AGENTS.md`, `required-skills.yml`, the snapshot and provenance when
applicable, and the installed conductor at `$SKILLS_DIR/sdlc/SKILL.md`.

### Additional skills

The kit does not manage skills outside `required-skills.yml`. Install any additional skill of your choice
for the project.

Teams may add `test-driven-development` when they want strict TDD for all behavior changes. The
kit's default remains the proportional policy in `docs/test-strategy.md`.

The optional `improve` skill can audit a completed epic or suggest a direction with `improve next`.
It remains outside the pipeline. Install it only where you want it available and route selected
directions through Stage 1 with `sdlc {chosen direction}`.

## 3. Adapt the project

Projects may skip this section only when their tracker, CI commands, and skill setup match the
defaults. Otherwise, adapt them before relying on the workflow.

### Tracker

GitHub Issues is the default. If the project uses Linear or Jira, replace these integration points
without changing the surrounding workflow:

| Responsibility | GitHub default | Replacement |
| --- | --- | --- |
| Create tasks | `gh issue create` in `$SKILLS_DIR/sdlc/SKILL.md` | Tracker API or CLI |
| Report status | `gh issue list` or `gh project item-list` in `$SKILLS_DIR/project-status/SKILL.md` | Tracker query |
| Complete tasks | `Closes #N` in `$SKILLS_DIR/sdlc/SKILL.md` | Native Git integration or post-merge update |
| Name branches | Issue number in `$SKILLS_DIR/feature-start/SKILL.md` | Tracker key such as `ENG-123` |

### CI and end-to-end tests

Before relying on CI, replace the commands in `.github/workflows/ci.yml` with the project's lint,
typecheck, test, and build commands. Existing CI must pass. An unreachable workflow blocks Land.

Use the platform's E2E runner: Playwright for web, or Maestro or Detox for mobile. A Playwright MCP
server is optional and useful only for interactive browser work.

## 4. Smoke test

Ask the agent to start `sdlc`. A fresh installation should find `> STATUS: TEMPLATE` in
`docs/context.md`, begin Stage 0, and stop at the context gate. It must not enter Spec before Stage 0
is complete.
