# Install

The installer adds the kit to one project. It never overwrites an existing destination and uses a
project-local skills directory by default. It does not use a registry.

## Prerequisites

You need:

- A POSIX system (Linux or macOS, including WSL). Windows is unsupported: the installer relies on
  POSIX file semantics and atomic no-replace renames.
- Bash and Python 3.10+.
- Filesystems that support descriptor-relative operations and atomic no-replace renames
  (`renameat2` on Linux, `renameatx_np` on macOS).
- Git 2.25 or newer.
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
| — | `.sdlc-kit-version` (release marker, updated on upgrade) |
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

The installer stages each publication in a temp file or directory and renames it into place. If an
install stops partway through, the next real install checks the target root, template-file parents,
and configured skills root under their publication locks. It removes only regular files named
`.sdlc-file-` plus 24 lowercase hexadecimal characters, and directories named `.sdlc-skill-`, a
sanitized skill label, and a 24-character lowercase hexadecimal token. Ambiguous lookalikes and the
legacy `.sdlc-staging-intent` marker are left untouched; `.sdlc-preserved-*` directories from older
releases remain for manual inspection. Legacy `.sdlc-file-<24hex>` directories from the old 0.7.x
publisher are also skipped; inspect their contents and remove them manually if they are leftovers.
The installer records the release in `.sdlc-kit-version` at
the target root, or `unreleased` when this checkout has a non-empty `[Unreleased]` changelog section;
this marker is the one destination it updates when the value changes.

### Upgrade an existing installation

Installs record what they published in `.sdlc-kit-manifest.json`.
Upgrading is then one command — the installer replaces files it published that the adopter never
edited, keeps adopter-modified files and reports them, and deletes files the new release removed
when you never edited them:

```bash
# Preview what would change
SKILLS_DIR="$SKILLS_DIR_ABS" ./install.sh --upgrade --dry-run "$TARGET"

# Apply
SKILLS_DIR="$SKILLS_DIR_ABS" ./install.sh --upgrade "$TARGET"
```

Upgrade semantics:

- The manifest (`.sdlc-kit-manifest.json`) is self-contained: each recorded file carries its
  routing class and the base content the kit last laid down — no snapshot directory in your
  tree.
- A file whose content still matches its base is an untouched kit copy → replaced with the new
  release's content.
- A living file (the kit's skills, `AGENTS.md`, `docs/context.md`, `docs/test-strategy.md`, the
  published GitHub templates) that you edited is **three-way merged** with the new version
  against that base: disjoint edits apply cleanly (`M` lines — review the hunks); overlapping
  edits keep your copy untouched and write a conflict-marked resolution file next to it, named
  `<file>.sdlc-conflict` (`C` lines). That file already holds every non-conflicting kit change, so
  resolve its marked regions and move it over your copy; deleting it drops those changes. Then
  mark it resolved (below) so the next upgrade merges from the new version. A kit change that only
  rewords a placeholder line you filled is ignored rather than conflicting.
- A filled template instance (`docs/specs/`, `docs/changes/`, `docs/adr/`, `docs/contracts/`,
  `docs/architecture.md`, `docs/threat-model.md`) is adopter-owned once filled: kit template drift is never merged into
  it. It is kept and reported (`!` lines).
- A CI workflow (`.github/workflows/`) runs as installed, so an upgrade never replaces, merges, or
  deletes it, even unedited. A changed kit template is reported (`!` lines) for you to compare by
  hand.
- A pinned snapshot (`frontend-design`) must stay byte-identical; if you edited one, the
  upgrade reports the divergence instead of merging.
- A merged file re-anchors on the new kit version, so the next upgrade merges the next delta
  instead of replacing your merged content. Manifest records never adopt your file's content
  as the kit's — consecutive upgrades cannot mistake your edits for kit output.
- Manifests from versions 1 and 2 have no reliable anchor (v2 records could conflate adopter
  content with kit content): adopter-modified files are kept and reported with a hand-verify
  note instead of merged or replaced.
- A file removed upstream is deleted when it still matches its base (`-` lines), along with any
  directory that leaves empty. An edited, adopted, or untracked file removed upstream stays on disk
  and is reported (`!` lines).
- The version marker and `.sdlc-kit-manifest.json` update to the new release. The obsolete
  `.sdlc-kit-base/` directory, if a version-2 install created one, is removed, and so is any
  `.sdlc-vendor/` metadata older installers left in skill directories, with directories that leaves
  empty.

Merges are textual: a clean merge can still read oddly where an edit removed a rule the new
version rewrites. The `M` lines are the short list to eyeball, not a rubber stamp.

**Installs made before this installer existed** have no manifest. The upgrade command changes
nothing and prints the one-time manual path. To adopt manifest-based upgrades once: stop agents,
move each skill directory you want refreshed out of `SKILLS_DIR_ABS` to a backup, run
`./install.sh "$TARGET"` (it re-adds the kit files), delete any installed files the release
removed, and verify. After that first run, the manifest exists and later upgrades run
automatically.

Always stop agents that use the target before upgrading, and read `CHANGELOG.md` for what the
release touched.

#### Adopting a file (`--adopt`)

Some files can never track the kit template: a filled doc whose template evolves (`docs/context.md`),
a CI workflow you rewrote for your stack, a template you deleted on purpose. Each upgrade would
otherwise re-attempt a merge it cannot complete, regenerating a `.sdlc-conflict` file or re-adding
the deleted file every run. Adopt the path once to stop that:

```bash
SKILLS_DIR="$SKILLS_DIR_ABS" ./install.sh --upgrade --adopt docs/context.md --adopt .github/workflows/ci.yml "$TARGET"
```

An adopted path is never written, merged, or re-added again (`A` lines; present files report when
the kit template changed upstream). A plain install re-adds missing adopted files.

#### Marking a hand merge resolved (`--resolved`)

After you resolve a conflict, or rework an adopted file to the current template, tell the
installer the file now matches this kit version:

```bash
SKILLS_DIR="$SKILLS_DIR_ABS" ./install.sh --upgrade --resolved AGENTS.md --resolved docs/context.md "$TARGET"
```

The file is kept as it is (`R` lines); its base moves to the current kit version, any adoption
ends, and its `.sdlc-conflict` file is removed. Later upgrades merge only what changes after this
version. A file that still holds conflict markers is refused.

If the runtime does not read `AGENTS.md`, point its instruction file to it:

```text
@AGENTS.md
```

## 2. Bundled skills

The installer copies these skills to the configured `SKILLS_DIR`. It does not use a registry.

| Skill | Upstream | Used |
| --- | --- | --- |
| `bootstrap` | sdlc kit | Once per project: foundation docs and a check proven to fail |
| `grilling` | mattpocock/skills (maintained adaptation) | Planning, when a request leaves decisions open |
| `frontend-design` | anthropics/skills (pinned snapshot) | Building UI |
| `code-review` | sdlc kit | The reviewer, before every PR |
| `security-review` | sdlc kit | Plan and review of trust-boundary changes |
| `address-review` | sdlc kit | Manual: triage review comments on an open PR |
| `unslop` | Cursor pstack (maintained adaptation) | Applied to human-facing prose |

Browser checks while building use the harness's browser tool. If yours has none, install Anthropic's
`webapp-testing` skill from [anthropics/skills](https://github.com/anthropics/skills); it needs
Python and Playwright.

`vendor/skills/` holds the one snapshot the kit does not maintain (`frontend-design`), installed
as-is and pinned in [`vendor/skills.lock.json`](./vendor/skills.lock.json). Each maintained
adaptation names its upstream in its header and ships the upstream license.

Skills are optional accelerators. The installed `AGENTS.md` carries the gates and no-compromise
rules on its own, so a harness that cannot invoke skills still runs the workflow. When a skill is
available, use the project-local copy first, then a user-global one, then the harness's equivalent.

Skills run with the agent's permissions. Commit the project-local copies so every contributor and CI
run uses the same instructions.

### Claude Code and `CLAUDE.md`

Claude Code v2.1.277 and later reads `AGENTS.md` directly when no `CLAUDE.md` exists. The kit still
installs a one-line `CLAUDE.md` containing `@AGENTS.md`: it costs nothing, never loads `AGENTS.md`
twice, and keeps working on older versions, in sessions where native `AGENTS.md` support is off, and
when a contributor adds a `CLAUDE.local.md` (which otherwise stops Claude Code reading `AGENTS.md`).

### Additional skills

The kit does not manage skills outside `required-skills.yml`. A project may add any skill; adding
one does not make it part of the workflow.

## 3. Adapt the project

### Tracker

GitHub Issues is the default. Projects without an external tracker keep slices as a checklist in the
change proposal. `docs/context.md` → Lifecycle names the tracker; adopting one midway moves only the
open proposals' unticked slices into it. For Linear or Jira, replace these integration points:

| Responsibility | GitHub default | Replacement |
| --- | --- | --- |
| Create slice issues | `gh issue create`, after plan approval | Tracker API or CLI |
| Complete slices | `Closes #N` in the PR | Native Git integration or a post-merge update |
| Name branches | `feat/{issue number}-{slug}` | Tracker key such as `ENG-123` |

### CI and tests

Replace the placeholder step in `.github/workflows/ci.yml` with the project's toolchain setup and
check command, keeping every action pinned to a commit SHA. The template fails until you do, so a
missing check cannot pass silently. `bootstrap` then proves each part of the check fails on a planted
error.

Set the test layers and tools in `docs/test-strategy.md`. Use the platform's end-to-end runner, such
as Playwright for web or Maestro for mobile.

## 4. Smoke test

Ask the agent to run `bootstrap`. A fresh installation should find `STATUS: TEMPLATE` markers,
fill the foundation, and stop at the foundation gate without starting a plan.
