<!-- Copied to .github/pull_request_template.md by install.sh. Aligns PRs with the pipeline. -->

## What & why

<!-- One or two lines. Link the PRD and the issue. -->
Closes #

- PRD: `docs/prd/...`
- ADR(s): `docs/adr/...` (if a decision was made)

## Acceptance criteria

<!-- Copy the criteria from the PRD/issue and check them off. -->
- [ ] {criterion}

## Contract

- [ ] Implements against the frozen contract; no undocumented endpoints/fields
- [ ] Types generated from the contract, not hand-duplicated
- [ ] N/A — this change doesn't touch a contract

## Definition of Done (see AGENTS.md)

- [ ] Tests at the right layer; suite green
- [ ] App run / change observed working
- [ ] CI green (lint, typecheck, test, build)
- [ ] DB changes follow expand/contract (or N/A)
- [ ] Docs updated (`architecture.md` / ADR) as needed

## Security

- [ ] Touches a sensitive area (canonical list in `AGENTS.md` → Sensitive areas) →
      `docs/security.md` updated + `security-review` run
- [ ] N/A — not a sensitive area
