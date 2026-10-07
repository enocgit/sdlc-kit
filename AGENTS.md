# Maintainer guide

> These instructions govern this repository. The adopter-facing operating manual is
> `templates/AGENTS.md`; keep the two files separate.

## Repository purpose

`sdlc` is a portable workflow kit for teams that use coding agents. It packages kit-owned skills,
exact third-party snapshots, installation-safe scripts, and project-document templates. This
repository ships the kit; it does not run the pipeline itself — governance lives in this file and
`CHANGELOG.md`.

## Source of truth

- `skills/` contains kit-owned skills and the conductor.
- `vendor/skills/` contains the one unchanged third-party snapshot the kit does not maintain.
- `vendor/skills.lock.json` records snapshot identity and licensing; `.agents/skills/` holds the
  kit's own pinned copy of its writing-standards skill.
- `templates/` contains files published into adopter repositories.
- `required-skills.yml` is the supported-skill manifest.
- `scripts/` contains installer, vendoring, and validation code.
- `README.md`, `INSTALL.md`, and `CONTRIBUTING.md` describe the public maintainer workflow.

## Non-negotiable invariants

- Keep every file under a pinned snapshot directory (`vendor/skills/frontend-design/`,
  `.agents/skills/writing-clearly-and-concisely/`) byte-for-byte equal to its recorded pin in
  `vendor/skills.lock.json`.
- Do not hand-edit `vendor/skills.lock.json` hashes. Update a snapshot by replacing its tree at
  the new upstream commit, recomputing the per-file hashes, and recording the commit; review the
  resulting diff.
- Keep installation project-local by default, offline, reproducible, and non-destructive. An explicitly
  selected `SKILLS_DIR` may be external.
- Preserve no-clobber publication, containment, integrity, and restrictive-umask guarantees when
  changing installer code; an interrupted install may leave one temp directory for the next run to
  clean.
- Apply the maintained `skills/unslop` policy automatically to human-facing replies and prose where
  applicable; preserve its exclusions for code, contracts, commands, logs, quoted text, fixed formats,
  vendor snapshots, and neutral technical records.
- Keep the kit runtime-neutral. Skill invocation routes project-local → user-global → runtime
  equivalent; a runtime that cannot invoke skills consumes `AGENTS.md` alone.
- Do not add tests for prose, formatting, trivial syntax, or one-time repository absence. Use the
  smallest concrete verification that matches the risk; non-trivial executable behavior, including
  validation, authorization or security denial, error, retry, timeout, and partial-failure branches,
  still needs focused automated coverage. Start bug fixes with a
  failing automated test or observable reproducer appropriate to the risk, and start non-trivial
  executable behavior with a failing test (RED → GREEN); presentation-only copy, styling, or markup
  bugs may use a failing diff, render, or visual reproducer. Defer only conditions whose required
  deployed consumer, real data, deployment, load, traffic, or multi-version compatibility
  is unavailable, and record each deferral.
- Project-facing PRDs, ADRs, contracts, architecture, security docs, runbooks, test strategies,
  tracker items, and code comments must describe the product and its decisions, not this kit's
  internal mechanics. Templates may contain the instructions needed to fill them.
- Do not add agent self-attribution to commits, pull requests, or source comments.

## Disagreement

Challenge the plan before implementing it, and never open with agreement. That the maintainer asked
for it is not evidence that it is right, and neither is the fact that you wrote it.

- State the approach you rejected and why, and the failure you think most likely.
- Point at what decides the question: an invariant, a check, a file, or a measurement. Run a cheap
  check when one is available; before execution, name the observation that would settle the objection
  and collect it at the applicable gate instead of arguing from a position.
- Once the evidence is in, say which way it points and stop arguing. An objection with no way to
  falsify it is noise.

This mirrors the adopter-facing `Challenge before agreeing` rule in `templates/AGENTS.md`; keep the
two in step.

## Editing policy

- Prefer a small direct change over a new abstraction or compatibility layer.
- Preserve upstream snapshots where a narrow routing or integration rule is enough. Adapt or replace
  a snapshot only when its behavior reliably conflicts with this repository's needs.
- When a kit-owned skill or template changes, update its manifest, summaries, installation guidance,
  and focused validation as applicable.
- Keep `templates/AGENTS.md` at or below 150 lines and keep `templates/CLAUDE.md` as a one-line
  pointer.
- Use Conventional Commits when the maintainer requests a commit: `type(scope): summary`,
  imperative, at most 72 characters. Reference the relevant issue when one exists.

## Lifecycle

- **Stage:** live — adopter repositories consume released kit files; this checkout has no runtime
  service consumers.
- **Real data / production traffic:** none. Re-evaluate this register if the product adds one.

## Learnings

- Agents read the router and skip referenced files, and harnesses without skills read only
  `AGENTS.md`: keep stage procedure in `skills/sdlc/SKILL.md` and the gates in
  `templates/AGENTS.md`; `scripts/validate-kit.py` asserts the operative ones.
- Measure real line counts before writing a size target into a plan; estimated baselines have been
  wrong before.
- A runtime editor formatter can dirty committed files after the commit. Before binding review or
  evidence to a head, check the tree is clean at that head and revert formatting-only churn; it
  recurs on every edit.

## Verification

Run the smallest relevant checks while editing, then run the release checks before declaring the
change ready:

```bash
./scripts/validate-kit.sh
python3 scripts/validate-required-skills.py required-skills.yml
bash -n install.sh scripts/*.sh
python3 -m py_compile scripts/*.py
git diff --check
```

Also inspect the final diff, verify changed paths are present in `scripts/kit-manifest.txt`, and
confirm vendor snapshots are unchanged unless the task explicitly refreshes one. Documentation changes that affect links or rendering need link or rendering inspection;
presentation-only styling, markup, attributes, or copy may use a diff or one visual check, while
styling, markup, or attributes that change accessibility, security, or interaction behavior need
focused behavior evidence. Installer-affecting changes need a temporary-install
observation.

## Git and release safety

- Keep `main` deployable. Use a short-lived `feat/*` branch for changes.
- Do not commit, push, or open a pull request unless the user explicitly asks. The human performs every landing merge into the target branch. Local default-branch synchronization via `git merge --ff-only` and unreferenced synthetic merge/integration commits used only for review evidence are not landing merges.
- Do not invent remotes or transports. Surface authentication failures and point to the documented
  one-time fix.
- Update `CHANGELOG.md` for user-visible changes and review release metadata before publishing.
- Never treat a green local check as permission to bypass a required review or human decision.
