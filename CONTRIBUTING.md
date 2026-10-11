# Contributing to sdlc

Thanks for helping improve this workflow kit. This repository packages a Bash installer,
Python publication and validation tools, YAML manifests, Markdown templates,
and `SKILL.md` files. It has no build step.

## Keep changes focused

- Preserve runtime neutrality. Skill invocation routes project-local → user-global → runtime
  equivalent; a runtime that cannot invoke skills consumes `AGENTS.md` alone.
- Keep the gates, the review order, and the no-compromise rules in `templates/AGENTS.md`; some
  harnesses read only that file, and agents skip referenced files.
- Apply the deletion test before adding a rule: keep it only if a current frontier model with no
  instruction would get it wrong.
- Use `{placeholder}`, not `<placeholder>`; angle brackets break Markdown previews. Keep template
  comments in `<!-- ... -->`.
- Strengthen an existing step before adding one. Keep bug fixes and chores off the planning path.

## Add a maintained skill

Put kit-owned skills in `skills/{name}/` and declare them with `kind: local` and the matching
`sourcePath` in `required-skills.yml`. If you modify a third-party skill or technique for this kit,
treat it as a maintained adaptation: keep it under `skills/{name}/`, preserve its attribution and
license, and identify the adaptation clearly. Do not put modified content in `vendor/skills/`; that
directory is for unchanged pinned snapshots.

For every maintained skill, validate frontmatter, match the skill's `name` to its directory, and
write a clear trigger description.

## Add a vendored skill

Vendoring is for a third-party skill whose behavior the kit preserves unchanged. Declare
`vendor/skills/{name}/` as its `sourcePath` with `kind: vendored` in `required-skills.yml`, and add
a pin to `vendor/skills.lock.json`: the upstream repository URL, the pinned commit, the license,
and a `files` mapping of per-file SHA-256 hashes (see the `frontend-design` entry for the shape).
Each new snapshot pin is an explicitly approved decision — prefer a maintained adaptation.

To update the snapshot: replace the pinned tree with the upstream content at the new commit,
recompute the `files` hashes (`sha256sum` per file, relative to the skill directory), and record
the new commit and any license change. Review the resulting diff.

`scripts/validate-kit.sh` verifies every pin against the lock. Maintained adaptations are never
pinned there; their upstream license ships inside the skill directory.

## Open a pull request

1. Keep the change focused and reference its issue when one exists.
2. Update the `Unreleased` section of `CHANGELOG.md` for user-visible changes.
3. When workflow behavior changes, update `AGENTS.md`, `templates/AGENTS.md`, the affected skills,
   and any affected summaries, walkthroughs, templates, installation docs, and regression checks.
4. Install Python 3.10+ and PyYAML, then run `./scripts/validate-kit.sh` as part of the complete
   [verification checklist](./AGENTS.md#verification). The script checks critical installer safety,
   manifests, snapshot pins, and the workflow rules in the files agents read; the linked checklist covers the
   remaining release checks.
