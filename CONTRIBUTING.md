# Contributing to sdlc

Thanks for helping improve this workflow kit. It's a set of portable markdown templates and
`SKILL.md` files — no build step.

## What this repo is (and isn't)

- **Is:** a tool-agnostic, plan-gated pipeline (templates + skills + docs) teams drop into their
  projects.
- **Isn't:** a runtime or framework. Keep everything portable — plain markdown, no lock-in to a
  specific agent.

## Ground rules

- **Stay tool-agnostic.** No hard dependency on one agent runtime. Agent-specific accelerators
  are fine only as *optional* conveniences with a documented manual fallback.
- **Keep the conductor lean.** Stage detail belongs in the referenced skills/templates, not in
  `skills/sdlc/SKILL.md`.
- **Templates render cleanly.** Use `{placeholder}` (not `<placeholder>` — that's parsed as HTML
  and breaks markdown preview). Keep comments as `<!-- ... -->`.
- **Don't add stages lightly.** Nine (0–8) is already a lot; prefer strengthening an existing stage.
  Every addition must respect the right-sizing/fast-path principle.

## Editing skills

Use `skill-creator` to scaffold/validate `SKILL.md` frontmatter. Each skill's `name` must match
its directory; keep `description` specific and trigger-rich (it drives auto-activation).

## PRs

- One focused change per PR; reference the issue.
- Update `CHANGELOG.md` (Unreleased section).
- If you change the pipeline, update **all** of: `README.md`, `AGENTS.md`, the conductor skill,
  and `EXAMPLE.md` so stage numbers stay consistent.
