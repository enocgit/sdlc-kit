# Stage 7 — Land

Read this before any Stage 7 work. **GATE — the human merges.** The tracker-transition rules this
stage acts on are restated below (`references/rules.md` stays canonical for capability routing and
ci rules).

## Tracker transitions in force here

- **GitHub:** the PR carries `Closes #N` only when the change completes a pre-existing issue; the
  issue stays open through Land and the merge closes it — never close it by hand.
- **Linear/Jira with a configured Git integration:** reference the native key per that
  integration's convention; verify the integration is actually wired before relying on it.
- **Linear/Jira without an integration, or local-only:** no closing keyword anywhere. The task
  moves to _in review_ at Land and completes only after the merge; an alternate tracker's close is
  an outward-facing write — confirm before making it.
- **Local-only:** `docs/progress.md` _is_ the tracker. After the merge, check out and sync the
  default branch first (committing on the just-merged `feat/*` strands the update on a dead
  branch), move the row to `Done`, and land it by remote state.
- **Tracker follows capability** (rules.md): a remote present after a local-only decomposition
  migrates at the next task boundary — land the migration instead of new rows; never reaffirm
  local-only because the remote's issues are still empty.
- A configured PR or CI workflow that is **unreachable is a blocker, not a mode** — surface the
  fix and stop; never route around required checks or branch protection.

## Sequence

A merge-conflict resolution during Land is part of the reviewed change: disclose it in the PR body
or the stop report; if it alters code behavior (doc-wording resolutions do not), run a scoped
fresh-context re-review before the merge gate.

1. Confirm local readiness is complete (Stage 6). Required CI is a remote merge gate, never a
   reason to duplicate the suite locally; it need not be green before the PR opens.
2. Open the PR where hosting supports it; the PR text follows `AGENTS.md`'s writing standard and
   the PR template. **GitHub:** the PR carries `Closes #N` when the change completes a pre-existing
   issue — never create an issue just to have one to close. Other trackers or local-only: no
   closing keyword; move the task to _in review_ per `references/rules.md` → Task completion by
   tracker.
3. Report the stop in one line — PR link, CI pending, merge after green — and stop; do not poll. A
   single status glance to catch an instant failure is fine; a later failure is a normal fix, not a
   babysat turn. Do not restate what the PR body or the tracker already states: the delivery recap
   and checklist live there, not in the stop message. The report always names the Stage 6 review
   outcome — who reviewed it (fresh-context lanes or the named substitute) and the final verdict —
   a Land report without it is incomplete.
4. When CI finishes green, run the final Definition of Done confirmation (`definition-of-done-review`)
   and report whether the change is ready to merge. Green required CI is confirmed here, at the final
   merge-readiness check.
5. **GATE:** the human merges — always, in every capability mode. Commit, push, and the PR needed
   no ask; the merge is the one decision that is never the agent's. In local-only mode the combined
   ask ("approve commit and merge to the local default branch?") is the merge gate — execute the
   merge after approval and verify the result. Merge ownership is never delegated.

Once the push/PR is done, announce the gate in one line and stop:

> `SDLC ▸ Stage 7/8 Land · next gate: merging — merge when ready; I verify once you confirm.`

No merge-preparation essay, no second approval request — the merge gate was announced at the CI
seam. Resume when the human confirms the merge (local-only: resume immediately after the combined
merge ask is honored).

## After the merge (Land's tail)

Complete the task transition per `references/rules.md` → Task completion by tracker, then proceed
to Stage 8. Never pre-empt the transition before the merge: until the human merges, the honest
state is _in review_, and an abandoned or rejected PR must not leave a task reading done.

## Next

After the merge and tracker close-out, run the Retro: read `references/stage-8.md` before acting on it.
