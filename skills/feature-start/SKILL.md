---
name: feature-start
description: >
  Starts implementation of one decomposed task: isolates a workspace (a feature branch by default;
  a git worktree only when isolation is critical), loads the relevant PRD, ADR, and frozen contract,
  then discloses a compact in-session plan; approval before code is required only for sensitive work
  or a plan that deviates from the approved decomposition.
  Use at the start of Stage 4 (Implement) once scope is approved, or when the user says
  "start working on issue #N",
  "begin this task", or "let's implement {feature}".
---

# feature-start

Prepare a clean starting point with the context needed to implement one task, then disclose its plan.
Pause for approval before code only when the task is sensitive or the plan deviates from the approved
decomposition.

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
     setup and build commands as needed, then establish only a change-appropriate baseline — apply
     the verification standard in `AGENTS.md` (proportional evidence, no full suite by default) at
     pre-change scope: a focused test or runtime observation for behavior or interaction, a
     targeted render/browser or manual visual check for visual UI behavior, focused behavior
     evidence for accessibility or security changes in styling, markup, or attributes, and a source
     or context baseline for presentation-only markup, copy, or styling. If the selected baseline
     is red, stop and report; do not start work on a broken baseline. For non-trivial executable
     behavior, name a failing automated test in the task plan and create or run it after disclosure (and approval when required);
     an observational check alone is not sufficient. For other bug fixes, an existing focused check
     or observation that intentionally reproduces the known bug is an expected RED signal, not a
     broken baseline; record that observed failure in the task plan. If no such check exists, name
     the planned RED check and its expected failure in the task plan, then create or run it after
     disclosure (and approval when required). Unrelated setup, build, or baseline failures still block.
3. **Load context.** Read into context:
   - `docs/context.md` (domain, glossary, hard constraints — incl. retro learnings from prior cycles)
   - The feature's PRD in `docs/prd/`
   - Any ADR(s) it depends on in `docs/adr/`
   - The frozen contract artifact (OpenAPI/tRPC/schema) the task implements against
   - `docs/test-strategy.md` (Definition of Done + which layer to test at)
4. **Plan.** Present a compact in-session plan. Human approval is required only for a sensitive task
   or a plan that deviates from the approved decomposition; otherwise disclose the plan and proceed.
   If the runtime provides a structured plan artifact, use it; otherwise present the same plan in the
   response. The plan is a transient gate artifact,
   not repository documentation. Do not create `docs/superpowers/plans/` or another plan file unless
   the human asks for a durable plan.

   Keep it proportional to this one task and easy to scan:
   - **Outcome** — one sentence.
   - **Affected files** — exact paths and why each changes.
   - **Approach** — a few logical implementation steps, with verification paired to the risk.
   - **Verification** — name automated coverage for non-trivial executable logic, including validation,
     authorization or security denial, error, retry, timeout, and partial-failure branches; name focused
     behavior evidence or runtime observation for accessibility, security, and interaction behavior in
     styling, markup, or attributes; use a diff or one visual check for presentation-only markup,
     attributes, copy, or styling; or a link or rendering check for documentation that affects links
     or rendering, or a schema or generation check for configuration or generated output. For non-trivial
     executable behavior, name the planned failing
     automated test. For other bug fixes, name a planned failing automated test or observable reproducer
     appropriate to the risk; if an existing check or observation already fails, record its result,
     otherwise record the expected failure and create or run the check after disclosure (and approval when required).
   - **Risks and case against:** record four separate facts:
     - **Rejected approach** — what you rejected and why.
     - **Likely failure** — the failure most likely to occur.
     - **Least-confidence area** — where the plan is least certain.
     - **Settling observation** — the observation or evidence that would settle the objection.
     The plan gate requires all four elements; do not omit them. After the check runs, record its
     observed result and resulting direction at the applicable gate; before then, name the prospective
     observation.

   Omit implementation code, repeated PRD/ADR/contract content, speculative work, mechanical
   microsteps, and commit instructions. After the plan is disclosed (and approved when required),
   create or run the recorded planned RED check for a bug fix; for non-trivial executable behavior,
   create or run the failing automated test, then make it pass and refactor. Otherwise collect the
   planned proportional verification; presentation-only styling, markup, attributes, copy, or layout
   can use a diff or one visual check, while styling, markup, or attributes that change accessibility,
   security, or interaction behavior need focused behavior evidence.
5. **Conditional gate.** Present the plan. If the task touches a sensitive area or the plan deviates
   from the approved decomposition, stop and ask for approval before writing code. Otherwise disclose
   the plan and proceed; the human can interrupt at any time.

## Rules

- Implement against the frozen contract. If it is wrong, stop and raise it. A shipped contract with
  a deployed consumer requires the versioning/deprecation ADR and its approval before changing the
  interface. If there is no deployed consumer, apply the ADR matrix, obtain applicable approval, and
  re-freeze the contract before changing the interface.
- Amend a wrong ADR in the same change as the code and name the failed assumption. Edit a Proposed
  or Accepted ADR in place only while it is unimplemented and dependency-free; after amending an
  accepted ADR, renew human approval and re-freeze any affected contract. Supersede an implemented
  or depended-on ADR regardless of status, renew human approval before implementation resumes, and
  re-freeze any affected contract. Every PRD requirement or scope amendment returns to human approval.
  Take a reversal that invalidates the rest of the plan to the plan gate.
- Cover executable validation, authorization or security denial, error, retry, timeout, and
  partial-failure behavior. Defer only cases whose required deployed consumer, real data, load,
  staging or production traffic, deployment, compatibility, or multi-version condition is unavailable;
  put each deferral in the production register.
- If the task is bigger than ~a day of work, propose splitting it before starting.
- **Keep the SDLC status header** on every user-facing message, just like the conductor — open with
  `SDLC ▸ Stage 4/8 Implement · task #N · {next: plan approval / …}`. You're inside the pipeline even
  though `sdlc` isn't the active skill; don't drop the header once implementation starts.
- Don't commit or push unless asked.
