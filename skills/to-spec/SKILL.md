---
name: to-spec
description: "Turn the current conversation into the feature PRD: no interview, just synthesis of what you've already discussed."
disable-model-invocation: true
---

A maintained adaptation of Matt Pocock's `to-spec` skill from
[mattpocock/skills](https://github.com/mattpocock/skills) (MIT — see `LICENSE` in this directory).
The synthesis method is kept; the output is re-scoped for this kit's Stage 1, as stated in the
body below.
This skill takes the current conversation context and codebase understanding and produces the
feature PRD. Do NOT interview the user; just synthesize what you already know.

**Write the PRD with the kit's template** (`docs/prd/TEMPLATE.md`) to
`docs/prd/NNNN-{slug}.md`, and do not publish or label a tracker issue — tracker work begins at
Stage 3. The template below maps onto the kit template's sections: user stories feed Users &
goals and Requirements, implementation decisions feed Key decisions and Data & contract impact,
testing decisions feed the test strategy, and Out of scope feeds Scope.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

   Check with the user that these seams match their expectations.

3. Write the PRD using the kit's `docs/prd/TEMPLATE.md`, filling it from the synthesis above.
   The section map below says where each part of the upstream synthesis lands. Do not publish or
   label a tracker issue.

<spec-template>

The synthesis content, mapped onto the kit PRD template's sections:

- **Problem Statement, Solution, User Stories** → Users & goals, Requirements, and the Problem
  section. Keep stories in the "As an <actor>, I want a <feature>, so that <benefit>" form;
  extensive coverage is the point.
- **Implementation Decisions** → Key decisions (the decision itself, linked to an ADR when one
  exists) and Data & contract impact. No file paths or code snippets — they go stale; the one
  exception stands: inline a prototype-derived snippet only when it encodes a decision more
  precisely than prose (state machine, reducer, schema, type shape), trimmed to the
  decision-rich parts.
- **Testing Decisions** → feed `docs/test-strategy.md` and the acceptance criteria's verification
  steps; only external behavior is testable, and prior art in the codebase wins.
- **Out of Scope** → Scope: Out.
- **Further Notes** → Risks, Constraints, or Links as they fit.

</spec-template>
