# PRD 0002 — Vendoring rework

> Scan-first. Approval: pending. Scope: `vendor/` tooling and the vendored-skill boundary only —
> no pipeline behavior changes. Amends nothing in PRD 0001; this is the 0.9.0 feature PRD.
> Delete unused sections in the filled PRD. State nothing about implementation progress — the
> tracker owns live state; this document's delivery record is written once, when the feature is
> true.
>
> **Amending an approved PRD:** write a new amendment PRD that states the changed requirements and
> supersedes the superseded ones; link both directions. Do not rewrite approved requirements in
> place.

## Summary

Rework how third-party skills are carried. Three pipeline-critical skills move from exact
snapshots to maintained adaptations the kit owns; the six remaining snapshots keep their
byte-for-byte guarantee but pin to upstream tags instead of drifting branches; and
`scripts/vendor-skills.py` loses the crash-recovery machinery, mirroring the 0.8.0 installer
treatment. Target release: **0.9.0**.

## Delivery record

Written once at final reconciliation (2026-09-24):

- **Shipped:** all four plan items — the three forks (brainstorming, improve-codebase-architecture,
  webapp-testing; visual companion dropped per the dated amendment), tag-pin support with
  `--track`, the tool shrink, and the manifest/validation sync. Vendor holds six snapshots;
  `writing-plans` pins `refs/tags/v6.3.0` (same commit as its old main pin).
- **Pin exceptions, per the approved rule:** the PRD said "newest tag containing the pin", but
  executing it would have advanced content for five of six skills — their pins sit ahead of or
  between upstream tags, and `anthropics/skills` (irrelevant after the webapp-testing fork) has no
  tags at all. The no-content-change constraint wins: the rule as executed is "newest tag pointing
  exactly at the pin"; only `writing-plans` qualified. `to-spec`, `grilling`,
  `documentation-and-adrs`, `frontend-design`, and `ponytail` keep `refs/heads/main` tracks with
  the reviewed commits unchanged.
- **Evidence:** `validate-kit.sh` green (14 checks, including vendored removal and tamper
  detection against the new tool); `vendor-skills.py verify` and `sync` round-trip green;
  `--track` switch verified content-neutral (same commit, same hashes); adaptation-header license
  check added to the validator and green across all seven adaptations.
- **Metric:** scripts total went 3,591 → 3,113 (−478), not the PRD's ~2,050 target: the PRD
  baseline misread 0.8.0's actual scripts total (3,591, not 3,006 — the 0.8.0 figure excluded
  `validate-required-skills.py`), and the ~400 tool estimate ignored the irreducible
  verify/install/publish core. Final `vendor-skills.py`: 887 lines (from 1,371).
- **Friction notes (dogfood):** the exact-tag containment check before acting on FR-2 caught a
  silent content-advance the PRD as written would have caused — the grilling pass over the plan
  paid for itself; an annotated tag resolves to its tag object on `ls-remote`, which surfaced as a
  failed `--track` switch and was fixed in `resolve_commit` (peeled-ref preference) before any
  lock write succeeded.
- **Residual risks:** the five main-track snapshots still drift between deliberate refreshes —
  mitigated by reviewed pins and `verify`; `.vendor-old` mid-swap recovery is next-run rather
  than same-run, so a failed publication leaves `vendor/` briefly absent until the next vendor
  command (behaviorally covered by the removal and install checks).

## Key decisions

- **FR 1 — Fork three skills as maintained adaptations.** `brainstorming` (obra/superpowers,
  MIT), `improve-codebase-architecture` (mattpocock/skills, MIT), and `webapp-testing`
  (anthropics/skills, Apache-2.0) become kit-owned skills under `skills/`, following the
  `code-review` pattern: adaptation header naming the upstream and the re-scoping, upstream
  LICENSE retained in the skill directory. The conductor overrides that today live as notes in
  `required-skills.yml` (artifact paths, no `docs/superpowers/plans/`, no worktree prerequisite)
  are baked into the forked skill bodies. Amended 2026-09-24 during review: the brainstorming
  **visual companion is dropped** — the browser mockup server (`scripts/`, `visual-companion.md`,
  ~1,480 lines of untested executable code and the kit's only Node dependency) stays upstream; the
  fork carries the method prose, the spec-reviewer prompt, and a note that visual questions stay
  in the terminal. The `improve-codebase-architecture` fork likewise drops `agents/openai.yaml`;
  both drops are recorded in the adaptation headers.
  The three snapshots leave `vendor/` via `vendor-skills.py remove` — never a hand deletion.
- **FR 2 — Tag-based pins for the six remaining snapshots** (`to-spec`, `grilling`,
  `documentation-and-adrs`, `writing-plans`, `frontend-design`, `ponytail`). Rule: switch a
  skill's `track` to the newest upstream tag that **contains its currently pinned commit**; no
  content changes in this feature — content refreshes remain a deliberate separate act. A pin no
  tag contains (or a repo with no tags — `anthropics/skills` has none, which affects only
  `frontend-design` once `webapp-testing` is forked) keeps the `refs/heads/main` track, and the
  exception is recorded in this PRD's delivery record, not in the generated lock. `update`
  gains a `--track` argument so tracks move through the tool, never by hand-editing the lock.
- **FR 3 — Shrink `vendor-skills.py`** from 1,371 lines to roughly 400: remove the
  staging-intent file, quarantine, transaction marker, and inherited-lock recovery machinery;
  use a plain `flock`, stage in a temp directory, publish with an atomic no-replace rename, and
  clean another run's leftovers on the next run. The 0.8.0 installer guarantees carry over:
  containment, no-clobber, restrictive umask, dry-run, symlink validation, and behavioral tests
  for the denial and partial-failure branches. Subcommands `verify`, `verify-installed`,
  `sync`, `update`, `remove`, and the hidden installer wrappers (`install-locked`,
  `preview-locked`) survive; `continue-locked` / `continue-preview-locked` disappear with the
  machinery that needed them, and `install.sh` is updated to match.
- **FR 4 — Manifest and validation sync.** `required-skills.yml` re-kinds the three forks as
  `local` (stage routing and fallbacks preserved, now pointing at `skills/`);
  `scripts/kit-manifest.txt` covers the new paths; `validate-kit.py` checks that every
  maintained adaptation under `skills/` carries its adaptation header; README/INSTALL vendor
  wording matches. The AGENTS.md vendor invariants stay true as written.
- **Metric, correcting the Q10 estimate:** the earlier "~1,300 scripts after 0.9.0" was
  miscomputed. Measured arithmetic: 3,006 − (1,371 − ~400) ≈ **~2,050** lines across
  `install.sh` + `scripts/`. That is the honest target.

## Non-goals

- No content refresh of the six remaining pins (same commits as 0.8.0 unless a tag-containing
  rule forces nothing anyway — it cannot change content by construction).
- No new vendored skills, no additional forks, no vendor schema change (lock version stays 2).
- No pipeline or stage-behavior changes; `rules.md`, stage references, and templates are
  untouched except where they name vendor paths.

## Constraints

- AGENTS.md invariants: snapshots byte-equal to their pinned commits; vendor locks, provenance,
  and licenses only via `scripts/vendor-skills.py`; installation project-local, offline,
  reproducible, non-destructive; no-clobber, containment, restrictive umask preserved.
- Forks are permitted only with explicit approval (this PRD is that approval, per the invariant's
  carve-out).
- Runtime-neutral: dropped `agents/openai.yaml` is the only removal from forked content; else
  forks are unmodified copies plus header and baked overrides.

## Acceptance criteria

- `vendor/skills/` holds exactly six snapshots; `vendor-skills.py verify` green; each lock entry
  tracks a tag ref except documented main-track exceptions.
- The three forks exist under `skills/` with adaptation headers, retained licenses, baked
  overrides, and no runtime-specific files; `validate-required-skills.py` green against the
  updated manifest.
- `vendor-skills.py` ≤ ~450 lines; temporary-install observation passes (vendored skills install
  from the lock, dry-run inert, interrupted-run leftovers cleaned); full release checks green.
- CHANGELOG carries the 0.9.0 entries and a migration note for projects referencing the forked
  skills' vendor paths.
