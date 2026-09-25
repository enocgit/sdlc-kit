# Stage 5 — QA

Read this before any Stage 5 work. This stage is **proceed-with-disclosure**: verify, report, and
continue. The verification standard is `AGENTS.md`; the stage-to-check mapping is
`references/rules.md` → Verification.

## What QA produces

Change-scope evidence that the change works, proportional to its risk — the smallest local check
that proves the change, broadened for shared paths, contracts, or sensitive areas. CI green now or
after PR creation (the CI seam: with a PR workflow, local QA and review finish first; the single
commit/push/PR approval happens at the end of Stage 6 — `references/rules.md` → The CI seam).

## Tooling

- Use the project's own test runner and lifecycle commands.
- `webapp-testing`: its SKILL already scopes itself to UI flows, the project's lifecycle runner,
  and app-specific readiness signals; follow it as written.
- When a browser is and isn't the right evidence, and the RED → GREEN requirement, see
  `references/rules.md` → Verification.
