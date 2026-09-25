---
name: sdlc
description: >
  Orchestrates an end-to-end, plan-gated software build pipeline: routes each stage to the right
  skill while enforcing human approval gates. Covers discovery, PRD, stress-test, architecture,
  API contracts, decomposition, implementation, QA, review, landing, and retro. The single entry
  point for the workflow. Use when the user wants to build a feature or product the disciplined
  way, start or resume structured development, asks "what stage are we at" / "what's next", or
  says "start the sdlc" / "run the pipeline".
---

# sdlc — the conductor (router)

You are running a fixed, plan-gated pipeline. Your job is to (1) determine the current stage,
(2) read that stage's reference before acting, and (3) **STOP at every gate** for explicit human
approval. You guide; you do not silently skip ahead.

## Read order (non-negotiable)

1. Read `AGENTS.md` — the operating manual owns communication, documentation writing standards,
   Definition of Ready/Done, sensitive areas, and guardrails. This router and the stage references
   own pipeline mechanics; where they overlap, `AGENTS.md` wins.
2. Also read `docs/context.md` and `docs/test-strategy.md`.
3. **Before producing any stage output, read `references/stage-{N}.md`** for the stage you are
   entering. Never act from this router alone — the stage references own the procedure.
4. Cross-stage mechanics (tracker semantics, default-branch landings, verification, review
   topology, security-review coverage) live in `references/rules.md`. Read it whenever a stage
   reference points there.
5. Resolve skills: use the project's local bundled skill when present and invocable; if absent or
   not invocable, consult user-global directories (`~/.agents/skills`, `~/.claude/skills`); then
   a runtime equivalent; the manual `fallback` in `required-skills.yml` only as the last resort.

## Two altitudes

- **Project-level (foundation)** — set once at Stage 0: product PRD (`docs/prd/0000-product.md`),
  cross-cutting ADRs, architecture skeleton, foundational threat model, core contract.
- **Feature-level** — per feature (Stages 1–8): brief, PRD, ADR(s), contract slice.
  Don't design every feature up front; lock only what a first feature can't start without.

## Status header (every response)

Open every pipeline response with one line:

`SDLC ▸ Stage {N}/8 {Name} · {next gate or action}`

Examples: `SDLC ▸ Stage 0b/8 Foundation · next gate: approve foundation` ·
`SDLC ▸ Stage 4/8 Implement · task #5 · next: plan disclosure` ·
`SDLC ▸ Stage 6/8 Review · running security-review (sensitive area)`.
On-ramp sub-stages keep their letter (`0a`/`0b`/`0adopt`).

## Right-size the path

- **Feature / user-facing / risky** → establish Stage 0 once if needed, then Stages 1→8.
- **Bug fix / small enhancement** → Stages 4→5→6→7→8; reference an issue when one exists — never
  create one just for the reference; no PRD/contract/ADR.
- **Chore / docs / dep bump** → Stages 4→6→7→8; trivial diff, CI green before merge.
- Touching a **contract**, a **sensitive area**, or making a **decision** graduates a small change
  to the full path. When unsure, ask.
- Orient before routing: read the tracker (via `gh` / `project-status`) and the active PRD to infer
  the current stage and feature (local-only: `docs/progress.md`). State the chosen path, current
  stage, and next action before proceeding.

## The stages

| Stage | Use skill | Output | After producing output |
| ----- | --------- | ------ | ---------------------- |
| 0a Context (new) | installer templates (fill) | `AGENTS.md`, filled `docs/context.md` | **GATE — context filled** |
| 0b Foundation (new) | `documentation-and-adrs` | product PRD, foundational ADRs, architecture skeleton, core contract scaffold, threat model, configured `docs/test-strategy.md` | **GATE — approve foundation** |
| 0 adopt (existing) | `improve-codebase-architecture` + read-only analysis | reconstructed foundation (see `references/stage-0.md`) | **GATE — approve** |
| 1 Spec | `brainstorming` → `to-spec` → `grilling` | optional brief, then hardened PRD `docs/prd/NNNN-{slug}.md` | **GATE — approve PRD** |
| 2 Architecture + Contract | `documentation-and-adrs` + `grilling` | ADR(s), `docs/architecture.md`, `docs/security.md`, **frozen** contract | **GATE — approve approach + freeze interface** |
| 3 Decompose | `writing-plans` + `project-status` | tracker issues (or `docs/progress.md` rows) | disclose the breakdown, then continue |
| 4 Implement | `feature-start`; `frontend-design` (UI only), `ponytail` (backend/domain) | code on a `feat/*` branch, one task at a time | disclose the compact plan, then continue; **GATE only for a sensitive area or scope deviation** |
| 5 QA | proportional local verification + runtime checks | change-scope evidence; CI green now or after PR creation | proceed (disclose results) |
| 6 Review | `code-review`, `code-simplification`, `definition-of-done-review` | clean diff, local DoD evidence, findings fixed | inline; **`security-review` mandatory if a sensitive area is touched** |
| 7 Land | `project-status` | PR (or direct-merge path), tracker transition | **GATE — the human merges** |
| 8 Retro | reflect + write (native) | 0–3 durable learnings after every merge; final-child epic closure | offer to land repository edits |

## Gate discipline

- **GATE rows are hard stops.** Do not run the next stage's skill until the user approves. Skills
  are guidance injected into context — only YOU enforce these stops; be explicit every time.
- **Decompose, QA, Review are proceed-with-disclosure:** do the work, state what you did and any
  decision a human might override, and continue. The human can always interrupt.
- At every **GATE**: name the artifact and path, summarize in 2–4 lines, say what the next stage
  will do, and ask "Approve to proceed, or tell me what to change?" Stage-specific landing asks are
  specified in the stage references; landing mechanics live in `references/rules.md`.
- Keep gate prompts concise: artifact, decision, next action. Never append a second explanation of
  routine permissions or standing guardrails — follow them silently and report deviations.
- Before presenting gate artifacts, tracker issues, or PR text, review each point against the
  one-point writing rule in `AGENTS.md`.

## Borrow the technique, not the workflow

Community skills are **techniques**, not the pipeline: they were authored standalone and carry
opinions about where they write and what they do next that are wrong here. Run a borrowed skill's
method; override its workflow. Per-skill overrides (what to use, what to skip, where artifacts
land) are stated in the stage reference that invokes the skill. If a borrowed default fights an
`AGENTS.md` convention, `AGENTS.md` wins. Any skill that wants to open tracker issues or epics
defers to Stage 3 — the Spec stage produces a PRD, not issues.

## Referenced files

- Operating manual + standards: `AGENTS.md`
- Stage procedures: `references/stage-0.md` … `stage-8.md`
- Cross-stage mechanics: `references/rules.md`
- Templates: `docs/` (context, prd, adr, architecture, contracts, security, briefs, progress,
  test-strategy)
