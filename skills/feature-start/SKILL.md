---
name: feature-start
description: >
  Starts implementation of one decomposed task: isolates a workspace (a feature branch by default;
  a git worktree only when isolation is critical), loads the relevant PRD, ADR, and frozen contract,
  then proposes a compact in-session plan for approval before any code is written.
  Use at the start of Stage 4 (Implement) once scope is approved, or when the user says
  "start working on issue #N",
  "begin this task", or "let's implement {feature}".
---

# feature-start

Prepare a clean starting point with the context needed to implement one task, then stop for a plan
approval gate.

## Steps

1. **Pick the task — infer, don't interrogate.** Resolve the task's **identifier and slug** from
   the tracker and the user's request. The identifier is the GitHub issue number by default; on
   another tracker its key (`ENG-123`); in **local-only** mode the `#` column of the task table in
   `docs/progress.md`. Never invent one. One task per run. State the identifier and slug you
   resolved, then proceed; ask only when the request is genuinely ambiguous or no tracker entry
   matches.
2. **Isolate the workspace — default to a feature branch.** Create `feat/{id}-{slug}` directly.
   Use a git worktree only as an explicit manual escape hatch for opt-in parallel or disposable
   work, or when the user asks. Before changing anything, run `git worktree list --porcelain` and
   identify the primary checkout. Never switch or modify another checkout.

   Run these guards first:

   - **Clean tree:** Direct mode requires the idle primary checkout to have no uncommitted changes.
     Inspect ignored paths too (`git status --short --ignored`) before switching or synchronizing;
     if any uncommitted, ignored, or ambiguous path could be overwritten, stop and ask the human.
     A local-only `docs/progress.md` change may be committed only with explicit approval, and only
     from the primary checkout already on the default branch. A linked or topic checkout, and every
     temporary-worktree run, must stop until that tracker change is landed on the primary default
     path. Never silently omit it or commit it on an implementation branch.

   - **Fresh base:** Resolve `{default}` before branching. In direct mode, update the default branch
     from its configured upstream or from the one authoritative remote, using an explicit fetched
     target and `git merge --ff-only`; do not guess among multiple remotes. With no remote, use the
     local `refs/heads/{default}` ref and stop if it is absent. Verify the default branch is still
     the expected base after synchronization and rerun the clean-tree check immediately before
     creating the feature branch. If a remote is unreachable, do not call a cached ref fresh
     without evidence; let the human decide. A protected default uses the documented
     `plan/{NNNN}-{slug}` route.

     In temporary-worktree mode, do not switch an existing checkout. Fetch and compare the selected
     authoritative remote base when a remote exists; if the local `refs/heads/{default}` and fetched
     remote ref contain one another, select and record the containing full ref and its full
     `base_oid`. If they diverge, or the remote is ambiguous or freshness cannot be established,
     stop for a human decision. With no remote, require and use the fully qualified local
     `refs/heads/{default}` ref. The temporary-worktree command must use the recorded full
     `base_oid`, not re-resolve a mutable ref.

   - **Direct branch:** From the synchronized default branch, run
     `git switch -c "feat/{id}-{slug}"`; stop if it fails. Do not force checkout or overwrite
     ignored files.

   - **Opt-in temporary worktree:** This is a manual escape hatch, not an automatically provisioned
     workspace. The operator must supply an exact path in the platform's private temporary area,
     confirm it is new or empty, private, and outside every existing checkout, and perform any
     platform-specific path or alias verification. This kit does not create, inspect,
     canonicalize, ACL-protect, or otherwise enforce safety for that path.

     Record the exact `base_ref` and full `base_oid` from the Fresh base guard. Confirm the feature
     branch does not already exist, then run the generic Git-only recipe:

     ```text
     git show-ref --verify --quiet "refs/heads/feat/{id}-{slug}"
     git worktree add -b "feat/{id}-{slug}" "{worktree_path}" "{base_oid}"
     ```

     If the branch-existence command succeeds, stop. If `git worktree add` fails, retain the branch
     if Git created it and report the supplied path; never delete the branch automatically. Continue
     only after successful creation, and do not switch any existing checkout.

     After the task implementation is safely landed, or after setup/baseline/plan rejection before
     implementation, inspect the worktree. Use non-forced removal only after the status is confirmed
     clean and contains no tracked, untracked, or ignored content:

     ```text
     git -C "{worktree_path}" status --short --ignored
     git worktree remove "{worktree_path}"
     ```

     If status is dirty or cannot be inspected, or any output is present, leave the worktree and
     branch in place and report both for inspection. The generic removal command is the only cleanup
     this kit performs; the operator owns any parent-directory cleanup.

   - **Green baseline:** In the selected workspace, install dependencies and run the project's
     setup and build commands as needed, then establish only a change-appropriate baseline: use a
     focused test for behavior, a targeted render/browser or manual visual check for UI or styling,
     and a relevant link, schema, or syntax check for docs or configuration. Do not run the full suite by default; for shared paths, broaden verification to
     all impacted packages/modules. Reserve the full suite for broad or high-risk dependency
     fan-out or an explicit project rule. If the selected baseline is red, stop and report; do not
     start work on a broken baseline.
3. **Load context.** Read into context:
   - `docs/context.md` (domain, glossary, hard constraints — incl. retro learnings from prior cycles)
   - The feature's PRD in `docs/prd/`
   - Any ADR(s) it depends on in `docs/adr/`
   - The frozen contract artifact (OpenAPI/tRPC/schema) the task implements against
   - `docs/test-strategy.md` (Definition of Done + which layer to test at)
4. **Plan.** Present a compact in-session plan. If the runtime provides a structured plan artifact,
   use it; otherwise present the same plan in the response. The plan is a transient gate artifact,
   not repository documentation. Do not create `docs/superpowers/plans/` or another plan file unless
   the human asks for a durable plan.

   Keep it proportional to this one task and easy to scan:
   - **Outcome** — one sentence.
   - **Affected files** — exact paths and why each changes.
   - **Approach** — a few logical implementation steps, with verification paired to the risk.
   - **Verification** — name the check that proves completion: an automated test where logic
     changes, or a rendered-output, rendering, link, or schema check for markup, copy, styling, or
     configuration.
   - **Risks or open questions** — only when real.

   Omit implementation code, repeated PRD/ADR/contract content, speculative work, mechanical
   microsteps, and commit instructions. After approval, start a bug fix or non-trivial testable
   behavior with a failing test, then make it pass and refactor. Otherwise implement directly and
   collect the planned proportional verification; a static attribute, copy, or layout change carries
   no logic to cover, so inspect its rendered output rather than adding an assertion for it.
5. **GATE.** Present the plan. Ask for approval before writing any code.

## Rules

- Implement against the frozen contract. If it is wrong, stop and raise it: a contract change is a
  decision (new/updated ADR), never an inline edit.
- A wrong ADR or PRD is not a stop. Supersede it in the same change as the code and name the
  assumption that failed; take a reversal that invalidates the rest of the plan to the plan gate.
- Cover observed behavior, not hypothetical failures. While `docs/context.md` shows no deployed
  consumer, real data, or production traffic, do not add failure-path, load, or compatibility cases
  for conditions that cannot occur; put each deferral in the production register.
- If the task is bigger than ~a day of work, propose splitting it before starting.
- **Keep the SDLC status header** on every user-facing message, just like the conductor — open with
  `SDLC ▸ Stage 4/8 Implement · task #N · {next: plan approval / …}`. You're inside the pipeline even
  though `sdlc` isn't the active skill; don't drop the header once implementation starts.
- Don't commit or push unless asked.
