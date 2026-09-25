# Stage 7 — Land

Read this before any Stage 7 work. **GATE — the human merges.** Capability routing, CI rules, and
tracker transitions live in `references/rules.md` (Tracker and landing capabilities, The CI seam,
Task completion by tracker).

## Sequence

1. Confirm local readiness is complete (Stage 6). Required CI is a remote merge gate, never a
   reason to duplicate the suite locally; it need not be green before the PR opens.
2. Open the PR where hosting supports it; the PR text follows `AGENTS.md`'s writing standard and
   the PR template. **GitHub:** the PR carries `Closes #N` when the change completes a pre-existing
   issue — never create an issue just to have one to close. Other trackers or local-only: no
   closing keyword; move the task to _in review_ per `references/rules.md` → Task completion by
   tracker.
3. Report CI running and stop — do not poll. A single status glance to catch an instant failure is
   fine; a later failure is a normal fix, not a babysat turn.
4. When CI finishes green, run the final Definition of Done confirmation (`definition-of-done-review`)
   and report whether the change is ready to merge. Green required CI is confirmed here, at the final
   merge-readiness check.
5. **GATE:** the human merges — always, in every capability mode. A single approval may cover
   commit, push, and opening the PR when the request names all three; it authorizes exactly the
   actions named. Merge ownership is never delegated.

## After the merge (Land's tail)

Complete the task transition per `references/rules.md` → Task completion by tracker, then proceed
to Stage 8. Never pre-empt the transition before the merge: until the human merges, the honest
state is _in review_, and an abandoned or rejected PR must not leave a task reading done.
