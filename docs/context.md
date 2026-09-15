# Project context

## Product

`sdlc` is a portable workflow kit for software teams that use coding agents. It installs a
project-local conductor, operating rules, document templates, and pinned third-party stage skills.
The kit aims to make agent-led feature work reproducible without changing user-global skills.

## Users

- Maintainers review upstream skill revisions, publish kit releases, and keep installation safe.
- Adopters install the kit into new or existing repositories and adapt its defaults to their stack.
- Coding agents follow the installed conductor and stop at each human approval gate.

## Terms

| Term | Meaning |
| --- | --- |
| Kit-owned | Files maintained in this repository outside borrowed snapshot directories. |
| Snapshot | An unchanged third-party skill tree pinned to an immutable upstream commit. |
| Conductor | `skills/sdlc/SKILL.md`, which routes work through the pipeline. |
| Gate | A point where work stops until a human explicitly approves the next action. |
| Land | Getting a change onto its target branch: a default-branch commit at Stages 0, 2, and 8, or a human-merged PR at Stage 7. |

## Hard constraints

- Keep `vendor/skills/**` byte-for-byte equal to its pinned upstream content.
- Automatic and stage-bound installation stays project-local. A user-global optional companion is
  allowed only through a separate command the user explicitly chooses.
- Never overwrite an existing target file or skill directory.
- Do not commit, push, open pull requests, or merge unless the user asks.

## Out of scope

- Hosting a skill registry or agent runtime.
- Replacing a target project's tracker, CI provider, or deployment platform.
