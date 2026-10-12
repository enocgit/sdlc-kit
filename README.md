# sdlc

`sdlc` is a project-local workflow kit for building software with AI agents. It gives an agent a
repeatable way to plan, implement, verify, review, and land changes while recording the decisions
in the project.

The kit installs:

- a project operating manual from `templates/AGENTS.md`, installed as `AGENTS.md`: the rules, the
  two gates, and how a change moves from plan to merge;
- templates for specs, change proposals, ADRs, architecture, the threat model, and test strategy; and
- a few skills installed project-locally for reproducible runs: `bootstrap` for setup, `grilling`
  for planning, `code-review` and `security-review` for the reviewer, plus `address-review`,
  `unslop`, and a pinned `frontend-design` snapshot.

It works with any stack: web and API products, backends, CLIs, libraries, and mobile apps. Projects
set their own tools during bootstrap.

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

Follow the [adaptation guidance](./INSTALL.md#3-adapt-the-project) if the project differs from the
defaults. Then ask your agent to run `bootstrap`; after that, describe a feature or a bug.

The installer adds missing files, never overwrites existing destinations, and writes only to the
target project and any explicitly selected `SKILLS_DIR`. For a worked example,
read [`EXAMPLE.md`](./EXAMPLE.md). Maintainers should read
[`CONTRIBUTING.md`](./CONTRIBUTING.md). Questions, friction, or adoption feedback: open an issue at
<https://github.com/enocgit/sdlc-kit>.

## How the workflow works

The kit encodes what model upgrades do not supply: a maintainer's approval at the decisions that matter, a
living record of what the product does, review by a context that did not write the code, and checks
proven able to fail. It leaves step-by-step procedure to the agent and the harness.

1. **Plan** (features, and changes to a contract, trust boundary, or decision): `grilling` settles
   open questions, and the agent writes a change proposal with its spec delta, acceptance criteria,
   and a smoke check on realistic input. **Gate:** you approve the plan.
2. **Build** each slice on its own branch: a failing test first, then the code, the check command,
   the smoke check, and the spec update. Bug fixes and chores start here.
3. **Review** in a context that did not write the change, on a different model when one is
   available, before the PR opens.
4. **PR** with a "Where to look" section and a criterion-to-test proof table. **Gate:** you merge.

**Seven rules hold in every project:** a maintainer performs every merge; review runs in a fresh
context; trust-boundary changes get a security review; implementation never drifts from a frozen
contract; behavior ships with tests and each check is proven able to fail; the spec states what
shipped; no secrets in the repository. Everything else is a default a project may change in its
`AGENTS.md`.

**What you read instead of the code:** `docs/specs/` states current behavior with requirement IDs
that tests cite; each PR lists the hunks worth reading and the test proving each acceptance
criterion.

## Existing projects

Run the same installer. It adds missing files and leaves existing ones untouched; merge
`templates/AGENTS.md` and `templates/docs/` into the project's own files. `bootstrap` then
reconstructs specs, architecture, and the threat model from the code without changing behavior. To upgrade a previous
install, see [Upgrade an existing installation](./INSTALL.md#upgrade-an-existing-installation).

## Defaults and portability

- `AGENTS.md` is canonical and carries the gates and the review order on its own; a harness without
  skills reads the named skill files directly. The installed `CLAUDE.md` is a one-line `@AGENTS.md` import.
- The bundled `unslop` adaptation applies to human-facing prose, not to code, commands, logs, quoted
  text, or fixed formats.
- GitHub is the default tracker and PR host, not a requirement. Projects without an external
  tracker keep slices in the change proposal.
- Templates are stack-neutral. `bootstrap` sets the stack, check command, and test tools.
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
| `skills/` | kit-owned skills and maintained adaptations |
| `vendor/skills/` | the one pinned, unmodified third-party snapshot |
| `vendor/skills.lock.json` | upstream revisions, paths, content hashes, and license notes |
| `scripts/install-safe.py` | no-clobber publication, install manifest, and `--upgrade` engine |
| `templates/docs/` | project documentation templates |
| `templates/github/` | CI, issue, and pull-request templates |
| `required-skills.yml` | supported-skill manifest and where each skill is used |
| `scripts/validate-kit.sh` | maintainer validation and install smoke test |
