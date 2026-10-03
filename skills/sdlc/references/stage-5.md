# Stage 5 — QA

Read this before any Stage 5 work. This stage is **proceed-with-disclosure**: verify, report, and
continue. The verification standard is `AGENTS.md`; its operative core is restated here
(`references/rules.md` stays canonical).

## What QA produces

Change-scope evidence that the change works, proportional to its risk — the smallest local check
that proves the change, broadened for shared paths, contracts, or sensitive areas. CI green now or
after PR creation (the CI seam: with a PR workflow, local QA and review finish first; the single
commit/push/PR approval happens at the end of Stage 6 — restated in `references/stage-6.md`).

**Operative core:** a bug fix starts from a failing automated test or observable reproducer;
non-trivial executable behavior (validation, authorization or security denial, error, retry,
timeout, partial-failure branches) gets focused automated coverage, RED → GREEN; UI/browser checks
only when the change exercises a UI/browser flow — backend changes verify at the API level; a
full-suite run is never the local default.

## Tooling

- Use the project's own test runner and lifecycle commands.
- `webapp-testing`: its SKILL already scopes itself to UI flows, the project's lifecycle runner,
  and app-specific readiness signals; follow it as written.
- When a browser is and isn't the right evidence, see `references/rules.md` → Verification.

## Next

After this stage's gate approval or proceed-disclosure, announce Stage 6 and read
`references/stage-6.md` before acting on it — the skill alone is not the procedure.
