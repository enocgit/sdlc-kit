# Stage 0 — Context and Foundation

Read this before any Stage 0 work. Gate mechanics live in the router; the landing ask forms are
restated below (`references/rules.md` stays canonical).

## Stage 0 is incomplete when

- `AGENTS.md` is missing or still contains `Stack (placeholder`
- `docs/context.md` is missing, still has its `> STATUS: TEMPLATE` line or `{placeholder}` tokens,
  or lacks populated `## Lifecycle` and `## Production register` sections with current values,
  triggers, and owners
- `docs/test-strategy.md` is missing or still contains its `STATUS: TEMPLATE` marker or placeholder
  tools
- the product PRD (`docs/prd/0000-product.md`), `docs/architecture.md`, `docs/security.md`,
  `docs/contracts/README.md`, or the applicable decisions in `docs/adr/` are missing, templated,
  or contain placeholder tokens or example-only contract paths
- the ADR directory records no actual stack, repository, auth, datastore, or API decision
- `docs/security.md` has no project-specific foundational threats and mitigations

The installer pre-creates these paths — do **not** rely on existence alone.

If Stage 0 is incomplete, treat **"context filled" as a gate** and run the on-ramp below; do not
advance to Discovery until the STATUS markers are gone and the sections are completed for this
project.

## Bootstrap (new project, little or no code)

**0a Context** — the installer already scaffolded `docs/`, `AGENTS.md`, and the one-line
`CLAUDE.md` pointer; if any are missing, re-run the kit's `install.sh` (non-destructive) rather
than recreating them by hand. Adapt the stack and conventions in `AGENTS.md` and interactively fill
`docs/context.md`. Record one durable fact there: what exists **outside this repo** (or outside
your control) that imports, calls, or builds on the code — other repositories, published packages,
client apps or services, other teams. Stage 2's contract-freeze decision reads this recorded fact
instead of guessing. **GATE: context filled** — approval does not ask for a commit.

**0b Foundation** — produce the project-level artifacts:

- product PRD at `docs/prd/0000-product.md`
- the few unavoidable cross-cutting ADRs (stack, repo layout, auth, datastore, API style) in
  `docs/adr/NNNN-{slug}.md`
- `docs/architecture.md` skeleton
- core contract scaffold; **trim `docs/contracts/README.md` to real/`(future)` paths — never leave
  template examples**
- foundational threat model in `docs/security.md`
- `docs/test-strategy.md` configured with the real test tools

Keep it minimal: only decisions a first feature genuinely can't start without; let the rest emerge
per-feature. **GATE: approve the foundation before Discovery.** At this gate, ask to land the full
context + foundation package on `main`. Landing ask, by remote state:

- **No remote** → commit to the local default branch.
- **Remote, default branch unprotected** → commit and push it under the same approval.
- **Remote, default branch protected** → `plan/{NNNN}-{slug}` → PR → merge; wait for the human to
  confirm the package reached the default branch before Stage 1 starts.

## Adopt (existing codebase)

Use `improve-codebase-architecture` plus explicit read-only code analysis to reconstruct the
foundation: `docs/prd/0000-product.md`, `docs/context.md` — including the outside-consumer fact
above —, `docs/architecture.md`, `docs/security.md` for existing sensitive surfaces, and
backfilled foundational ADRs (stack, repo, auth, datastore already baked into the code). Configure `docs/test-strategy.md` from the existing
test setup. Point `docs/contracts/README.md` at the existing contract source. Record known
tech-debt / risky areas and actionable follow-up candidates in `docs/architecture.md`; do not
create issues during adoption — Stage 3 owns issue creation after foundation approval. Your first
workflow-validation feature starts at Stage 1. **GATE: approve**, then land the reconstructed
package at the combined Stage 0 gate using the landing ask forms above.

**Skill override — `improve-codebase-architecture`:** use only its code-reading and deepening
heuristics. In that snapshot, `CONTEXT.md` means `docs/context.md`; do not invoke its unavailable
`codebase-design` or `domain-modeling` skills; update `docs/context.md` directly when needed; skip
its CDN-backed HTML report. Write adoption findings into this kit's foundation artifacts.

## Merge rule for existing files

If `AGENTS.md` / `CLAUDE.md` / `docs/` already exist, do **NOT** overwrite. Merge: back up or
section-merge, preserve the team's content, surface conflicts. Never clobber.

## Next

After this stage's gate approval or proceed-disclosure, announce Stage 1 and read
`references/stage-1.md` before acting on it — the skill alone is not the procedure.
