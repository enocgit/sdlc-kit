# Maintainer guide

> These instructions govern this repository. The adopter-facing operating manual is
> `templates/AGENTS.md`; keep the two files separate.

## Repository purpose

`sdlc` is a portable workflow kit for teams that use coding agents. It packages kit-owned skills,
exact third-party snapshots, installation-safe scripts, and project-document templates. Read
[`docs/context.md`](./docs/context.md) for the maintained product context.

## Source of truth

- `skills/` contains kit-owned skills and the conductor.
- `vendor/skills/` contains unchanged third-party snapshots.
- `vendor/skills.lock.json`, `vendor/provenance/`, and `vendor/licenses/` record snapshot identity
  and licensing.
- `templates/` contains files published into adopter repositories.
- `required-skills.yml` is the supported-skill manifest.
- `scripts/` contains installer, vendoring, and validation code.
- `README.md`, `INSTALL.md`, and `CONTRIBUTING.md` describe the public maintainer workflow.

## Non-negotiable invariants

- Keep every file under `vendor/skills/**` byte-for-byte equal to its pinned upstream snapshot, except
  for an explicitly approved snapshot removal performed with `scripts/vendor-skills.py remove`.
- Do not hand-edit generated vendor locks, provenance, licenses, or snapshot files. Use
  `scripts/vendor-skills.py` for refreshes or approved removals and review the resulting diff.
- Keep installation project-local by default, offline, reproducible, and non-destructive. An explicitly
  selected `SKILLS_DIR` may be external.
- Preserve no-clobber publication, containment, recovery, quarantine, integrity, and restrictive-
  umask guarantees when changing installer code.
- Apply the maintained `skills/unslop` policy automatically to human-facing replies and prose where
  applicable; preserve its exclusions for code, contracts, commands, logs, quoted text, fixed formats,
  vendor snapshots, and neutral technical records.
- Keep the kit runtime-neutral. Agent-specific behavior needs a manual fallback.
- Do not add tests for prose, formatting, trivial syntax, or one-time repository absence. Use the
  smallest concrete verification that matches the risk; non-trivial behavior still needs a focused
  regression signal.
- Project-facing PRDs, ADRs, contracts, architecture, security docs, runbooks, test strategies,
  tracker items, and code comments must describe the product and its decisions, not this kit's
  internal mechanics. Templates may contain the instructions needed to fill them.
- Do not add agent self-attribution to commits, pull requests, or source comments.

## Disagreement

Challenge the plan before implementing it, and never open with agreement. That the maintainer asked
for it is not evidence that it is right, and neither is the fact that you wrote it.

- State the approach you rejected and why, and the failure you think most likely.
- Point at what decides the question: an invariant, a check, a file, or a measurement. Run a cheap
  check instead of arguing from a position.
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

## Verification

Run the smallest relevant checks while editing, then run the release checks before declaring the
change ready:

```bash
./scripts/validate-kit.sh
python3 scripts/vendor-skills.py verify
python3 scripts/validate-required-skills.py required-skills.yml
bash -n install.sh scripts/*.sh
python3 -m py_compile scripts/*.py scripts/validation/*.py
git diff --check
```

Also inspect the final diff, verify changed paths are present in `scripts/kit-manifest.txt`, and
confirm vendor snapshots are unchanged unless the task explicitly refreshes one. Documentation-only
changes need link or rendering inspection; installer-affecting changes need a temporary-install
observation.

## Git and release safety

- Keep `main` deployable. Use a short-lived `feat/*` branch for changes.
- Do not commit, push, open a pull request, or merge unless the user explicitly asks.
- Do not invent remotes or transports. Surface authentication failures and point to the documented
  one-time fix.
- Update `CHANGELOG.md` for user-visible changes and review release metadata before publishing.
- Never treat a green local check as permission to bypass a required review or human decision.
