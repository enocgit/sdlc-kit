# Contributing to sdlc

Thanks for helping improve this workflow kit. The repository contains a Bash installer, Python
safety and vendoring tools, YAML manifests, provenance metadata, Markdown templates, and `SKILL.md`
files. It has no build step.

## Rules

- Keep the kit runtime-neutral. Agent-specific shortcuts must remain optional and have a manual
  fallback.
- Keep `skills/sdlc/SKILL.md` focused on routing and gates; put stage detail in its skill or
  template.
- Use `{placeholder}`, not `<placeholder>`, because angle brackets break Markdown previews. Keep
  comments in `<!-- ... -->`.
- Strengthen existing stages before adding one. Preserve the right-sized paths for fixes and
  chores.
- Add skills maintained by this kit under `skills/{name}/` and declare them with `kind: local` and
  the matching `sourcePath` in `required-skills.yml`. For an adapted third-party technique, preserve
  its attribution and license while clearly marking the maintained adaptation. Optionally use
  `skill-creator` for substantial
  changes. Regardless of tooling, validate frontmatter, match each skill's `name` to its directory,
  and give it a clear trigger description.
- For a third-party skill, declare `vendor/skills/{name}/` as its `sourcePath` with
  `kind: vendored`, and register its upstream source in `vendor/skills.lock.json`. Run
  `python3 scripts/vendor-skills.py update {name}` to create or refresh the snapshot, license, and
  provenance. Never create or edit those generated files by hand; review their diff.

## Pull requests

1. Keep the change focused and reference its issue.
2. Update the `Unreleased` section of `CHANGELOG.md`.
3. When pipeline behavior changes, update the canonical rules and conductor plus affected
   summaries, walkthroughs, templates, installation docs, and regression checks.
4. Install Python 3.10+ and PyYAML, then run `./scripts/validate-kit.sh`. This command is a
   compact release gate for critical installer safety, manifest, provenance, and installed-integrity
   invariants.
