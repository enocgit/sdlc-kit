# Stage 1 — Spec

Read this before any Stage 1 work. Gate mechanics live in the router; landing mechanics in
`references/rules.md`.

## Output

An optional Stage-1 brief, then a hardened feature PRD at `docs/prd/NNNN-{slug}.md`. No tracker
issues exist yet — tracker work begins at Stage 3.

- **Brief** (`docs/briefs/NNNN-{slug}.md`): only for a fuzzy or speculative idea; a well-understood
  feature skips the brief and goes straight to the PRD.
- **PRD**: describe observable behavior and testable rules; state each requirement once with only
  the detail needed for approval and verification; define terms on first use.

## Skills, in order

1. `brainstorming` — explore → **one question at a time** → approaches → design. Discovery is
   exploratory — **no code.** The fork lands the approved brief at `docs/briefs/NNNN-{slug}.md`
   and stops; it owns no handoff to planning.
2. `to-spec` — turn the approved direction into the PRD using the kit's PRD template; write to
   `docs/prd/NNNN-{slug}.md`; do not publish or label a tracker issue.
3. `grilling` — stress-test the PRD until no open questions remain; the Definition of Ready
   requires this (Stage 1 resolves open questions during the stress-test).

**Skill overrides:**

- `to-spec`: use its synthesis method with the kit's PRD template; override its tracker publishing.
- `grilling`: point it at the decision, not the document.

## Gate

**GATE — approve PRD.** Present the PRD, summarize, and stop. Approval does not ask for a commit:
the approved PRD stays in the worktree while Stage 2 produces the ADRs, architecture, security
updates, and frozen contract; the Stage 1–2 planning package lands once, at the Stage 2 gate.
