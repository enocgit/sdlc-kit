# Change NNNN: {title}

> Copy to `NNNN-{slug}.md`. Delete unused sections and this note.

- **Status:** Draft | Approved | Shipped ({merge links}) | Dropped
- **Specs touched:** {`docs/specs/{area}.md`}

## Why

{The problem and who has it. Two or three sentences.}

## Spec delta

<!-- The requirements as they will read once shipped. On ship, apply them to the spec. -->

- **Added** {AREA}-N: {behavior}
- **Changed** {AREA}-N: {old} → {new}
- **Removed** {AREA}-N: {behavior and why}

## Acceptance criteria

<!-- At least one per added or changed requirement. -->

- [ ] {ID}: {observable outcome} ({unit | integration | end-to-end})

## Smoke check

<!-- One or two realistic inputs and what their user must get from each, in the user's words: a
     real page flow, request, caller, data sample, repository, or query. Point to the input (URL,
     command, path). It runs where `docs/test-strategy.md` → Local run covers it, and a maintainer
     runs it where Local run does not. It is a look at the running product, not a test. Never
     commit private data. With no real data yet, use the closest public sample. A change no user
     can see writes "none: no user-visible change". -->

- {realistic input} → {what the user must see or get}

## Approach

{The shape of the solution in a few lines. Link ADRs for hard-to-reverse choices.}

- **Contract:** {frozen artifact path, or none}
- **Trust boundaries:** {what changes and the threat it opens, or none}

## Out of scope

- {What this change deliberately does not do}

## Slices

<!-- One per reviewable PR; one slice needs no list. With a tracker, each becomes an issue after
     approval and this list links them; without one, tick each in the commit that completes it. -->

- [ ] {slice: acceptance criteria IDs, test layer}
