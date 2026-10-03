---
name: diagnosing-bugs
description: Root-cause procedure for bug-fix tasks — build a tight, red-capable feedback loop, minimise the repro, test ranked falsifiable hypotheses, then fix at a correct seam. Use at Stage 4 when the task is a bug fix, or when a reported failure has no known cause.
---

# Diagnosing bugs

Maintained adaptation of `diagnosing-bugs` from mattpocock/skills (MIT, bundled as
LICENSE). Re-scoped for this pipeline: Stage 4 bug tasks, kit communication and
verification rules, no bundled scripts. Skip a phase only with a stated reason.

Load context first: `docs/context.md`, the ADRs for the area you will touch, the
tracker record for the failing behavior, and `docs/test-strategy.md` for the
verification bar the fix must meet.

## Redact

Captured output can carry secrets. Replace every credential, token, and personal
value with `<REDACTED>` before it enters a report, plan, or commit. Build loops
against environment variables so credentials stay in the environment instead of in
what you show.

## Phase 1 — Build a feedback loop

This is the skill. A tight pass/fail signal that goes red on this bug makes
bisection, hypothesis testing, and instrumentation mechanical. Without one, no
amount of code reading finds the cause.

Construct one, in this order:

1. Failing test at whatever seam reaches the bug: unit, integration, e2e.
2. HTTP script against a running server, diffing observed against expected.
3. CLI invocation on a fixture input against a known-good snapshot.
4. Headless browser script asserting on DOM, console, or network (the Stage 5
   webapp-testing scope).
5. Replay of a captured trace through the code path in isolation.
6. Throwaway harness exercising the bug path with one call.
7. Property or fuzz loop for "sometimes wrong output" bugs.
8. Bisection between two known states, automated so `git bisect run` can drive it.
9. Differential run: the same input through the old and new version or config.

Then tighten it: faster (skip unrelated setup), sharper (assert the reporter's exact
symptom, not "didn't crash"), deterministic (pin time, seed randomness, freeze the
network).

Non-deterministic bugs: the goal is a higher reproduction rate, not a clean one.
Loop the trigger, parallelise, narrow timing windows until the failure rate is
debuggable.

When no loop can be built, stop and say so. List what you tried and ask for the
reproducing environment, a redacted captured artifact, or permission to add
temporary instrumentation. Do not hypothesize without a loop.

Phase 1 is done when one named command (a script path, a test invocation, a curl)
has run at least once — shown with redacted output — and is red-capable (it drives
the actual bug path and asserts this specific symptom), deterministic, fast, and
runnable unattended. Reading code for theories before that command exists is the
exact failure this phase prevents.

## Phase 2 — Reproduce and minimise

Run the loop. Confirm it fails with the symptom the report described, reproducibly
across runs, and capture the exact failure. Then shrink it: cut inputs, callers,
config, data, and steps one at a time, re-running after each cut, keeping only what
is load-bearing. A minimal repro shrinks the hypothesis space and becomes the
regression test.

## Phase 3 — Rank hypotheses

Generate three to five ranked hypotheses before testing any one of them. Each must
be falsifiable: "if X is the cause, changing Y makes the bug disappear." Discard or
sharpen any hypothesis that has no prediction. Report the ranked list with the loop
evidence at the stage's reporting point; if the reporter's context re-ranks it, take
the new order.

## Phase 4 — Instrument

One variable per probe, each probe mapped to a hypothesis from Phase 3. Prefer a
debugger or REPL to logs; prefer targeted logs at hypothesis-distinguishing
boundaries to logging everything. Tag every debug log with a unique prefix (for
example `[DEBUG-a4f2]`) so cleanup becomes one grep.

Performance regressions: measure before changing. Establish a baseline with a
timing harness, profiler, or query plan, then bisect against it.

## Phase 5 — Fix at a correct seam

Turn the minimised repro into a failing test at the seam where the bug actually
occurs, watch it fail, apply the fix, watch it pass, then re-run the Phase 1 loop
against the original, un-minimised scenario. This is this stage's failing-test rule
with the seam made explicit.

If no correct seam exists — the testable surface cannot replicate the failure chain
— that is a finding, not an inconvenience. Record it in the task and route the
structural change through the approach gate or an ADR instead of redesigning inline.

## Phase 6 — Clean up

Before declaring done: the original repro no longer fails; the regression test
passes, or the missing seam is recorded; a grep confirms no `[DEBUG-` instrumentation
remains; throwaway harnesses are deleted; and the verified hypothesis is stated in
the commit or PR message so the next debugger starts from it.
