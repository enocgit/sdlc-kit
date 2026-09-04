# Contributing to sdlc

Thanks for helping improve this workflow kit. This repository packages a Bash installer,
Python safety and vendoring tools, YAML manifests, provenance metadata, Markdown templates,
and `SKILL.md` files. It has no build step.

## Keep changes focused

- Preserve runtime neutrality. Agent-specific shortcuts stay optional and need a manual fallback.
- Keep `skills/sdlc/SKILL.md` focused on routing and gates. Put stage detail in the relevant skill or
  template.
- Use `{placeholder}`, not `<placeholder>`; angle brackets break Markdown previews. Keep template
  comments in `<!-- ... -->`.
- Strengthen existing stages before adding one. Preserve the right-sized paths for fixes and chores.

## Add a maintained skill

Put kit-owned skills in `skills/{name}/` and declare them with `kind: local` and the matching
`sourcePath` in `required-skills.yml`. If you modify a third-party skill or technique for this kit,
treat it as a maintained adaptation: keep it under `skills/{name}/`, preserve its attribution and
license, and identify the adaptation clearly. Do not put modified content in `vendor/skills/`; that
directory is for unchanged pinned snapshots.

For every maintained skill, validate frontmatter, match the skill's `name` to its directory, and
write a clear trigger description.

## Add a vendored skill

Declare `vendor/skills/{name}/` as its `sourcePath` with `kind: vendored`, and register the upstream
source in `vendor/skills.lock.json`. Run this command to create or refresh the snapshot, license,
and provenance:

```bash
python3 scripts/vendor-skills.py update {name}
```

Never create or edit those generated files by hand. Review the resulting diff.

To remove a vendored skill and regenerate the lock, license, and provenance metadata, use this only
for an explicitly approved snapshot removal:

```bash
python3 scripts/vendor-skills.py remove {name}
```

Maintainers need PyYAML. These commands restore locked content or verify it offline:

```bash
python3 scripts/vendor-skills.py sync
python3 scripts/vendor-skills.py verify
```

## Open a pull request

1. Keep the change focused and reference its issue when one exists.
2. Update the `Unreleased` section of `CHANGELOG.md` for user-visible changes.
3. When pipeline behavior changes, update `AGENTS.md`, `templates/AGENTS.md`, the conductor in
   `skills/sdlc/SKILL.md`, and any affected summaries, walkthroughs, templates, installation docs,
   and regression checks.
4. Install Python 3.10+ and PyYAML, then run `./scripts/validate-kit.sh` as part of the complete
   [verification checklist](./AGENTS.md#verification). The script checks critical installer safety,
   manifests, provenance, and installed integrity; the linked checklist covers the remaining release
   checks.
