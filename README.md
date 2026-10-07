# sdlc

`sdlc` is a project-local workflow kit for building software with AI agents. It gives an agent a
repeatable way to plan, implement, verify, review, and land changes while recording the decisions
in the project.

The kit installs:

- a conductor skill that routes work through the workflow;
- a project operating manual from `templates/AGENTS.md`, installed as `AGENTS.md`;
- templates for specs, change proposals, ADRs, architecture, security, contracts, and test strategy; and
- stage skills installed project-locally by default for reproducible runs — maintained adaptations
  the kit owns, plus exact third-party snapshots pinned under `vendor/skills/`.

It works with any stack: web and API products, backends, CLIs, libraries, and mobile apps. Projects
set their own tools at Stage 0.

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
target project and any explicitly selected `SKILLS_DIR`. For a worked example,
read [`EXAMPLE.md`](./EXAMPLE.md). Once the workflow is familiar, keep
[`CHEATSHEET.md`](./CHEATSHEET.md) nearby. Maintainers should read
[`CONTRIBUTING.md`](./CONTRIBUTING.md). Questions, friction, or adoption feedback: open an issue at
<https://github.com/enocgit/sdlc-kit>.

## How the workflow works

The kit encodes what model upgrades do not supply: human approval at the decisions that matter, a
living record of what the product does, review by a context that did not write the code, and checks
proven able to fail. It leaves step-by-step procedure to the agent and the harness.

| # | Stage | Main output | Stop |
| --- | --- | --- | --- |
| 0 | Foundation | context and lifecycle, spec skeleton, foundational ADRs, a check command proven to fail | approve foundation |
| 1 | Plan | change proposal with its spec delta; ADRs for hard-to-reverse choices; frozen contract for outside consumers | approve plan |
| 2 | Decompose | tracker tasks with acceptance criteria and test layers | disclose |
| 3 | Build | one tested, committed task; specs updated with it | disclose; gate on a trust-boundary change |
| 4 | Review | fresh-context `code-review`; `security-review` for trust-boundary changes | disclose |
| 5 | Land | PR with a "Where to look" section | the human merges |
| 6 | Retro | specs match what shipped; 0–3 learnings | disclose |

Bug fixes and chores start at Stage 3. A contract, trust-boundary, or decision change sends them to
Stage 1.

**Seven rules hold in every project:** a human performs every merge; review runs in a fresh
context; trust-boundary changes get a security review; implementation never drifts from a frozen
contract; behavior ships with tests and each check is proven able to fail; the spec states what
shipped; no secrets in the repository. Everything else is a default a project may change in its
`AGENTS.md`.

**What you read instead of the code:** `docs/specs/` states current behavior with requirement IDs
that tests cite; each PR lists the hunks worth reading and the test proving each acceptance
criterion; artifacts have line budgets so they stay readable.

## Existing projects

Run the same installer. It adds missing files and leaves existing ones untouched; merge
`templates/AGENTS.md` and `templates/docs/` into the project's own files. Stage 0 then reconstructs
specs, architecture, and security from the code without changing behavior. To upgrade a previous
install, see [Upgrade an existing installation](./INSTALL.md#upgrade-an-existing-installation).

## Defaults and portability

- `AGENTS.md` is canonical and carries the gates on its own; skills add per-stage detail where the
  harness supports them. The installed `CLAUDE.md` is a one-line `@AGENTS.md` import.
- The bundled `unslop` adaptation applies to human-facing prose, not to code, commands, logs, quoted
  text, or fixed formats.
- GitHub is the default tracker and PR host, not a requirement. Projects without an external
  tracker keep tasks in the change proposal.
- Templates are stack-neutral. Stage 0 sets the stack, check command, and test tools.
- `frontend-design` is pinned byte-for-byte in [`vendor/skills.lock.json`](./vendor/skills.lock.json);
  maintained adaptations name their upstream and ship its license.

## Repository map

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | maintainer-repository workflow rules, lifecycle, and learnings |
| `CHANGELOG.md` | release history; the installer reads the version from it |
| `templates/AGENTS.md` | operating-manual template installed in projects |
| `templates/CLAUDE.md` | one-line `@AGENTS.md` import for Claude Code |
| `install.sh` | merge-aware installer with `--dry-run` and `--upgrade` |
| `skills/` | conductor, kit-owned workflow skills, and maintained adaptations |
| `vendor/skills/` | the one pinned, unmodified third-party snapshot |
| `vendor/skills.lock.json` | upstream revisions, paths, content hashes, and license notes |
| `scripts/install-safe.py` | no-clobber publication, install manifest, and `--upgrade` engine |
| `templates/docs/` | project documentation templates |
| `templates/github/` | CI, issue, and pull-request templates |
| `required-skills.yml` | supported-skill manifest and stage bindings |
| `scripts/validate-kit.sh` | maintainer validation and install smoke test |
