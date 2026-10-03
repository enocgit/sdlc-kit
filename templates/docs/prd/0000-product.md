# Product PRD — {product name}

> Follow the documentation writing standard in AGENTS.md. This is the project-level product
> document, not a feature PRD. Record durable vision, boundaries, constraints, and links to
> foundational ADRs. Revise it as the product changes, and delete unused sections once filled.
> Keep it short: explain _why the product exists_, not how one feature works.

- **Status:** Draft | Approved | Living
- **Owner / date:** {name} / YYYY-MM-DD

## Vision

<!-- One paragraph: what this product is and the change it aims to make. -->

## Target users

- **{persona}** — who they are and the job they hire this product to do.

## Problems we solve

<!-- The core problems, in priority order. Tie back to docs/context.md. -->

- {problem} — for {persona}.

## Business model / how it sustains

<!-- Only if relevant: how it creates and captures value. -->

## Scope

**In (the product is):** <!-- the bounded thing we are building -->
**Out (the product is not):** <!-- explicit non-goals at the product level -->

## Success metrics (product-level)

<!-- The 1–3 numbers that say the product is working. Not feature metrics. -->

- {metric and target}

## Foundational decisions

<!-- Pointers to the cross-cutting ADRs that establish the foundation. -->

- Stack / framework → [ADR-NNNN](../adr/NNNN-{slug}.md)
- Repo layout (mono/poly) → [ADR-NNNN](../adr/NNNN-{slug}.md)
- Auth model → [ADR-NNNN](../adr/NNNN-{slug}.md)
- Primary datastore → [ADR-NNNN](../adr/NNNN-{slug}.md)
- API style (REST/tRPC/GraphQL) → [ADR-NNNN](../adr/NNNN-{slug}.md)

## Key constraints

<!-- Hard product-level constraints (regulatory, regional, platform). See docs/context.md. -->

## Roadmap shape (optional)

<!-- The rough sequence of initial features, if useful. -->
