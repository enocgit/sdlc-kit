# Contributing to sdlc

Thanks for helping improve this workflow kit. This repository contains portable Markdown templates and `SKILL.md` files. It has no build step.

## Rules

- Keep the kit runtime-neutral. Agent-specific shortcuts must remain optional and have a manual
  fallback.
- Keep `skills/sdlc/SKILL.md` focused on routing and gates; put stage detail in its skill or
  template.
- Use `{placeholder}`, not `<placeholder>`, because angle brackets break Markdown previews. Keep
  comments in `<!-- ... -->`.
- Strengthen existing stages before adding one. Preserve the right-sized paths for fixes and
  chores.
- Optionally use `skill-creator` for substantial skill changes. Regardless of tooling, validate
  frontmatter, match each skill's `name` to its directory, and give it a clear trigger description.

## Pull requests

1. Keep the change focused and reference its issue.
2. Update the `Unreleased` section of `CHANGELOG.md`.
3. When pipeline behavior changes, update `README.md`, `AGENTS.md`, `skills/sdlc/SKILL.md`, and
   `EXAMPLE.md` together.
4. Run `./scripts/validate-kit.sh`.
