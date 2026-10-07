# Project context

> STATUS: TEMPLATE — replace this marker and every `{placeholder}` at Stage 0.
> Loaded every session: keep durable facts only, ~120 lines at most. Link detail elsewhere.

## Product

<!-- What we're building, for whom, what success looks like. One paragraph. -->

## Lifecycle

<!-- Rules route on these values; a stale value misroutes them. -->

- **Team shape:** {solo | team}
- **Tracker:** {GitHub Issues | Linear | Jira | none: tasks live in each change proposal}
- **Deployed consumers:** {none | internal | external: who}
- **Real data:** {none | seed only | real rows in {tables}}
- **Production traffic:** {none | staging | live}

## Production register

<!-- Work we will owe and the event that forces it. Land an item before its trigger fires. -->

| Deferred | Trigger | Owner |
| --- | --- | --- |
| {e.g. API versioning} | First deployed consumer | {owner} |
| {e.g. expand/contract migrations} | First real row in the table | {owner} |
| {e.g. load tests and rate-limit hardening} | First production traffic | {owner} |

## Outside consumers

<!-- What outside this repo imports, calls, or builds on this code. Contract freezes read this. -->

- {consumer and what it consumes, or "none"}

## Glossary

| Term | Meaning |
| --- | --- |
| {term} | {definition an agent would otherwise guess wrong} |

## Hard constraints

- {constraint and why it exists}

## Learnings

<!-- Only traps that actually happened and a future agent would hit again. One dated bullet each, at most
     three lines, at most 30 bullets. A bug in the project is fixed, not recorded here. Prune fixed
     or covered bullets; promote rules that apply across features into AGENTS.md,
     docs/test-strategy.md, or an ADR. Not here: what shipped, why we chose X, system shape, what's
     next. -->

- **YYYY-MM-DD:** {the trap, and the rule that avoids it}
