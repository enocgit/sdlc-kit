# Change: {title}

> Copy to `{slug}.md`. Delete unused sections and this note. The PR that completes the change
> applies its spec delta and deletes this file.

- **Specs touched:** {`docs/specs/{area}.md`}

## Why

{The problem and who has it. Two or three sentences.}

## Spec delta

<!-- The requirements as they will read once shipped. -->

- **Added** {AREA}-N: {behavior}
- **Changed** {AREA}-N: {old} → {new}
- **Removed** {AREA}-N: {behavior and why}

## Acceptance criteria

<!-- At least one per added or changed requirement. -->

- [ ] {ID}: {observable outcome} ({unit | integration | end-to-end})

## Smoke check

<!-- Only for a change a user can see; otherwise delete this section. One or two realistic inputs
     and what their user must get from each, in the user's words: a real page flow, request,
     caller, data sample, repository, or query. Point to the input (URL, request, path), never a
     test command or fixture: a check CI could pass unattended is a test. It runs where
     `docs/test-strategy.md` → Local run covers it, and a maintainer runs it where Local run does
     not. Never commit private data. With no real data yet, use the closest public sample. -->

- {realistic input} → {what the user must see or get}

## Approach

{The shape of the solution in a few lines. Link ADRs for hard-to-reverse choices.}

- **Contract:** {frozen artifact path, or none}
- **Trust boundaries:** {what changes and the threat it opens, or none}

## Out of scope

- {What this change deliberately does not do}

## Slices

<!-- One per reviewable PR; one slice needs no list. Tick each in the PR that completes it. -->

- [ ] {slice: acceptance criteria IDs, test layer}
