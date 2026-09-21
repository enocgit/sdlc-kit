# Project context

> Follow the documentation writing standard in AGENTS.md. This file is loaded every session, so keep
> only durable domain facts and agent-critical gotchas. Link detail elsewhere.
>
> STATUS: TEMPLATE — replace this marker and every `{placeholder}` while completing the project context.
> Keep only durable facts that future contributors and agents need. This file loads every session, so
> prune stale entries rather than append.

## Product

<!-- What we're building, for whom, what success looks like. 1–2 paragraphs. -->

## Lifecycle

> STATUS: TEMPLATE — set the real values at Stage 0 and keep them current. Rules across the kit
> route on this block; a stale value silently misroutes them.

- **Stage:** {prototype | pre-production | internal | live}
- **Deployed consumers:** {none | internal only | external, and who}
- **Real data:** {none | seed only | real rows in {tables}, read or written by {process}}
- **Production traffic:** {none | staging only | live}

## Deferred for production

> Work we will owe, each with the trigger that forces it. Out of scope is a choice; this is debt
> with an owner and a tripwire. The promotion event that trips a trigger is a gate, so land the
> item before it.

| Deferred | Trigger that forces it |
| --- | --- |
| {e.g. API versioning and deprecation} | First external consumer |
| {e.g. expand/contract migration} | First write of real data |
| {e.g. failure-path, load, and compatibility tests} | First staging or production traffic |

## Personas

- **{persona}**: goals, constraints, what they care about.

## Glossary

<!-- Domain terms an agent would otherwise guess wrong. -->

| Term | Meaning |
|------|---------|
| {term} | {definition} |

## Hard constraints

<!-- Non-negotiables: regulatory, regional, technical, business. -->

- {constraint and why it exists}

## Out of scope (for now)

- {thing we are deliberately not doing}

## Learnings

<!-- Durable gotchas ONLY: things a future contributor or agent would get wrong without this line.
     Keep a flat list of dated bullets, each <=3 lines; no per-feature headings.

     Does NOT go here: what shipped (git/PR has it), why we chose X (ADR), system shape
     (architecture.md), what's next (the tracker), test approach (test-strategy.md), or process.

     Prune when you append: delete fixed gotchas, fold covered ones into their ADR/doc, and rewrite
     superseded bullets in place. Keep under ~30 bullets; at the cap, remove one to add one. -->

- **YYYY-MM-DD**: {the trap, and the rule that avoids it}
