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
| Land | Getting a change onto its target branch: a default-branch commit at Stages 0, 2, and 8, or a human-performed merge at Stage 7 (through a PR when available, directly when no PR workflow exists). |

## Lifecycle

- **Stage:** live
- **Deployed consumers:** adopter repositories consume released kit files; this checkout has no runtime service consumers
- **Real data:** none
- **Production traffic:** none

## Production register

> This kit has no runtime service, data store, or production traffic. Re-evaluate this register if
> the product adds one.

| Deferred | Trigger that forces it | Owner |
| --- | --- | --- |
| None currently | First runtime service, real data, or production traffic | Maintainer |

## Hard constraints

- Keep `vendor/skills/**` byte-for-byte equal to its pinned upstream content.
- Automatic and stage-bound installation stays project-local. A user-global optional companion is
  allowed only through a separate command the user explicitly chooses.
- Never overwrite an existing target file or skill directory.
- Do not commit, push, or open pull requests unless the user asks. Merge and landing ownership follow the Git and release safety rules in `AGENTS.md`.

## Out of scope

- Hosting a skill registry or agent runtime.
- Replacing a target project's tracker, CI provider, or deployment platform.

## Learnings

- **2026-09-24:** This repository does not self-host the sdlc pipeline: governance lives in
  `AGENTS.md`, `docs/context.md`, and `CHANGELOG.md`; planning artifacts are feature-branch PRDs
  (see `docs/prd/`). Do not scaffold adopter docs (ADR/, architecture, security) here.
- **2026-09-24:** `required-skills.yml` is deliberately yamllint-default-clean: block style,
  wrapped ≤80 columns. Keep new entries in that style instead of reintroducing flow mappings or
  long comment lines.
