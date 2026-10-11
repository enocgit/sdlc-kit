---
name: bootstrap
description: >
  Sets a project up for the workflow in AGENTS.md: fills docs/context.md, the spec skeleton, the
  test strategy, the threat model, and the architecture from the code or the product brief, and
  sets a check command proven to fail. Run once per project, while docs/ still holds STATUS:
  TEMPLATE markers, or when the user asks to set up or adopt the workflow.
---

# bootstrap

Done when these scans print nothing: no template marker or `{placeholder}` left, and no workflow
term in the product's files.

```bash
grep -rnE 'STATUS: TEMPLATE|\{[A-Za-z][^}]*\}' docs --exclude=TEMPLATE.md --exclude-dir=changes
grep -nE '\{[A-Za-z][^}]*\}' AGENTS.md
git grep --untracked -niE 'stage [0-6]|solo developer' -- . ':!AGENTS.md' ':!.agents' ':!*TEMPLATE.md' ':!.sdlc-kit-manifest.json'
```

## New project

Fill `docs/context.md` (product, Lifecycle, outside consumers, hard constraints), set the stack and
check command in `AGENTS.md`, set `docs/test-strategy.md`, and write only the ADRs a first feature
cannot start without. The human owns the Lifecycle values; propose them, never set them silently.
Describe only what exists; a plan labelled "intended" is still a plan and goes in the first change
proposal. With no code yet:

- `docs/architecture.md` keeps Context and one Parts row for the scaffold; delete Data, Key flows,
  and Cross-cutting until code exists.
- `docs/specs/README.md` lists areas without links until their spec exists.
- `docs/threat-model.md` may list trust boundaries the product will have, with control "none yet";
  a baseline control stays only if code or CI enforces it today. Records start empty.
- Write no product code; the checks need one trivial module and test.

## Existing codebase

Reconstruct the same set read-only from the code. Write specs for the areas that exist, backfill
ADRs only for hard-to-reverse choices already made, and fold any existing PRDs into specs. Keep the
kit's lines in `AGENTS.md` as written; project facts go in its project sections. Change the
existing CI to run the check command, or every part it runs, in the same change.

## Prove the checks

The check covers all the code, tests included. Fix existing failures or report them at the gate;
excluding code to get a part green is a skipped check. Plant one type error, run the check command,
see it fail at the typecheck, and revert; repeat for one failing test and one lint violation. One
plant per run, tripping only its own part. When the command chains named sub-commands
(`check:api`), a plant may run through the one that covers it; editor or harness diagnostics never
count. A check that fails on a clean tree is reported at the gate, not retried until it passes.

CI runs the same command. When the first PR's CI run finishes, read its log: lint, typecheck, and
tests each ran, and the test count matches the local run. A part that did not run is a bug to fix.

## Gate: approve foundation

Stop with three plain lines: what is done, anything unproven or skipped and why, and which files to
read. Commit nothing before approval. Then land it on the default branch:

- no remote → commit to the local default branch;
- remote with an unprotected default branch → commit and push, under the same approval;
- protected default branch → a branch and PR; the human merges.
