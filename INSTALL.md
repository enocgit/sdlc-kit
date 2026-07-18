# Installing the workflow

## Prerequisites

- **`git`** — required (branches, commits; the pipeline is GitHub-Flow based).
- **`gh` (GitHub CLI), authenticated** — required when GitHub provides the tracker or PR workflow.
  Issue creation at Decompose, PR opening at Land, and external `project-status` reports shell out
  to `gh` — not to any runtime's built-in GitHub tools. Run `gh auth login` with the **`repo`**
  scope, plus **`project`** if you use GitHub Projects (`gh project item-list` needs it; add later
  with `gh auth refresh -s project`). Skip only when neither the tracker nor landing workflow uses
  GitHub, such as a local-only project with no remote (see
  [Tool-specific nuances](#4-tool-specific-nuances)). Not needed for Stage 0–2 planning.
- **For projects with a remote, `git push` must work non-interactively** — the agent pushes the
  branch at Land (Stage 7) in a shell with no interactive prompt. After `gh auth login`, run
  **`gh auth setup-git`** so git authenticates GitHub over HTTPS with the `gh` token (no SSH key
  needed). **If your remotes are SSH** (`git@github.com:…`), route this repo over HTTPS — scope it
  to the project so you're not rewriting SSH globally:
  `git config --local url."https://github.com/".insteadOf "git@github.com:"` (run from inside the
  repo; or use `git remote set-url origin https://github.com/OWNER/REPO.git` for a single remote).
  Use `--global` only if you deliberately want *every* repo rewritten. Teams standardizing on SSH
  instead just need a working ssh-agent in the shell the agent runs in. Without this setup, a
  remote-backed push fails. A project with no remote skips this prerequisite; at Land, the human
  merges the local feature branch directly.
- **An agent that loads `SKILL.md` files** (Claude Code, Codex, Cursor, etc.) with shell access.

## 1. Copy the substrate into your project

The fastest path is `./install.sh /path/to/your/project` (merge-aware, never overwrites; add
`--dry-run` to preview). It copies all of the below. To do it by hand:

- `AGENTS.md` → project root
- `required-skills.yml` → project root (the installed conductor reads its `fallback:` entries when
  a routed skill isn't present — omit it and fallback routing silently fails)
- `templates/docs/` → project `docs/`
- `templates/ci.yml` → `.github/workflows/ci.yml`
- `templates/github/` → `.github/` (PR + issue templates aligned to the pipeline)
- `skills/` → your agent's skills directory (e.g. `.claude/skills/`, `.agent/skills/`, or
  wherever your runtime loads `SKILL.md` files)

Add a one-line `CLAUDE.md` (and `.cursorrules` if you use Cursor) at the project root:

```
See AGENTS.md for how we work on this project.
```

> **Where skills land.** The installer copies kit skills as **real directories** into `.claude/skills`
> (override with `SKILLS_DIR=...`). Real copies are portable and can't break. If you'd rather keep a
> single tool-agnostic source — e.g. alongside community skills the `skills` CLI installs into
> `.agents/skills` — point `SKILLS_DIR` at `.agents/skills` and symlink `.claude/skills → ../.agents/skills`
> yourself; the installer writes transparently through an existing symlink. **Caveat:** a symlink
> **dangles silently** if you ever delete its target (`.agents/skills`), and committed symlinks don't
> survive Windows-without-dev-mode, some CI checkouts, or Docker bind mounts — so the robust default is
> real copies.

## 2. Install community skills (portable SKILL.md, via skills.sh)

These cover most stages so we maintain less custom code. Source/availability varies by agent
runtime — confirm exact slugs and install commands at https://skills.sh. The same set is listed
machine-readably in [`required-skills.yml`](./required-skills.yml) (per-skill `kind`, `source`,
`stage`, and a manual `fallback` for runtimes that lack a given skill).

| Skill                                        | Source                                 | Used at stage                                                |
| -------------------------------------------- | -------------------------------------- | ------------------------------------------------------------ |
| `brainstorming`                              | obra/superpowers                       | 1 — Spec (discovery step; method only)                       |
| `to-prd`                                     | mattpocock/skills                      | 1 — Spec (PRD)                                               |
| `grill-me`                                   | mattpocock/skills                      | 1 — Spec (stress-test)                                       |
| `documentation-and-adrs`                     | addyosmani/agent-skills                | 0b Foundation & 2 — Architecture + Contract                  |
| `writing-plans`                              | obra/superpowers                       | 3 — Decompose                                                |
| `using-git-worktrees`                        | obra/superpowers                       | 4 — Implement (isolated workspace, opt-in; see `feature-start`) |
| `executing-plans`                            | obra/superpowers                       | 4 — Implement                                                |
| `frontend-design`                            | anthropics/skills                      | 4 — UI work                                                  |
| `test-driven-development`                    | obra/superpowers                       | 5 — QA                                                       |
| `webapp-testing`                             | anthropics/skills                      | 5 — QA (interactive browser checks)                          |
| `run`, `verify`                              | Claude Code native (else runtime equiv.) | 5 — QA                                                     |
| `code-review`, `simplify`, `security-review` | Claude Code native (else runtime equiv.) | 6 — Review                                                 |
| `improve-codebase-architecture`              | mattpocock/skills                      | 0 (adopt) — reverse-engineer an existing codebase            |

Install from the registry, e.g.:

```bash
npx skills add addyosmani/agent-skills/documentation-and-adrs
npx skills add obra/superpowers/writing-plans
# ...etc. Confirm exact install syntax at https://skills.sh
```

> **Don't assume any skill is pre-installed.** Some runtimes ship a few of these built-in;
> others ship none. Treat the table as the full set to provision on a fresh machine.
>
> **Vet before adopting.** Read each `SKILL.md` — confirm it's plain markdown (no runtime
> lock-in) and does nothing surprising. Skills run with your agent's permissions; a malicious
> or sloppy skill is a supply-chain risk. Prefer pinning to a release tag/commit.

### Highly Recommended companion skill (optional — not in the pipeline)

`improve` (shadcn, via skills.sh) is a **read-only advisor** that operates at a higher altitude than
any single stage. It's **not gated and not part of the 0→8 flow** — invoke it standalone, typically
**after an epic closes**, to survey what you just built. It ingests `docs/adr/`, PRDs, and
`context.md` during recon, so it composes with this kit's `docs/`. It **never edits code, merges, or
pushes**. Two distinct modes, with different relationships to the pipeline:

- **Audit (default `improve`)** → writes self-contained *fix* plans (bugs, debt, perf, test gaps,
  migrations) to `plans/`. This fills a gap the pipeline doesn't cover — Stage 1 discovers
  *features*, it doesn't audit the code. `--issues` can publish those plans as tracker issues.
- **Direction (`improve next`)** → surfaces 4–6 candidate directions with trade-offs. In this kit,
  treat it as **informational**: when it asks which suggestions to turn into design/spike plans,
  **decline** — carry the chosen direction into **Stage 1** (brief → PRD → issues) instead, so
  features flow through the pipeline. Left to its default it *will* write design/spike plans for
  whatever you select (fine for a throwaway spike, but not the feature path); declining is a usage
  discipline, not something the skill enforces.

- **Install it user-scoped**, not per-project — it's a cross-project advisor and that's how it's
  meant to be run (e.g. into `~/.agents/skills` symlinked into `~/.claude/skills`). A consumer who
  wants it committed per-repo can, but the default home is your user skills dir.
- **Don't confuse it with `improve-codebase-architecture`** (in the table above): that one is the
  *one-time Stage-0 `adopt`* reverse-engineer to bootstrap a foundation. `improve` is the
  *recurring post-epic* roadmap/audit. Different jobs.
- **The `plans/` directory is ephemeral roadmap output, not durable `docs/` "why".** Pick a team
  convention: gitignore it, or keep-and-delete once the plans are executed. Don't let it drift into
  a second source of truth alongside `docs/` and the tracker.
- **Landing a batch of generated plans:** open them as **dependency-ordered PRs** (least-coupled
  first) so conflicts stay small — but the **human still merges each one in order**. No auto-merge;
  the merge gate is never delegated to the agent (see `AGENTS.md` — merge is always the human's call).

## 3. Vendor + update policy (important — this pipeline leans on external skills)

`npx skills add` installs a **snapshot copy** into your skills directory. **Upstream updates do
NOT propagate automatically** — your installed copy is frozen until you re-install. This is good
for reproducibility but means you own keeping them current.

Recommended:

- **Commit the installed skills into your repo** (vendoring). They become reviewable, pinned,
  and reproducible for the whole team and for CI.
- **Update deliberately**, not silently: periodically re-add/`update`, then **diff and re-review**
  the change before committing — same scrutiny as a dependency bump.
- **Pin** to a tag or commit where the registry supports it, so installs are deterministic.

## 4. Tool-specific nuances

- **Skills directory** differs per runtime (e.g. `.claude/skills/`, `.agent/skills/`, Cursor's
  rules dir). Put the `skills/` contents where _your_ agent loads `SKILL.md` files.
- **`AGENTS.md` support varies.** If your tool doesn't read it natively, keep the one-line
  `CLAUDE.md`/`.cursorrules` pointer so the manual is still discovered.
- **Tracker is swappable (GitHub-first).** The tracker is the single source of truth. Against an
  external tracker there is **no in-repo mirror** and `project-status` only reads it; in local-only
  mode, `docs/progress.md` is the tracker and `project-status` maintains it. Retargeting to
  **Linear/Jira** is a *small manual port, not a config toggle* — the coupling is deliberately
  shallow (three skills + a couple of conventions), and the skill *logic* is tracker-agnostic, so
  you swap commands, not reasoning. **This is a good job to hand the agent:** point it at the
  touchpoints below and ask it to port them to your tracker's CLI/API cleanly — the shallow,
  well-scoped coupling is exactly what an agent ports reliably. Review its diff (auth, the
  auto-close convention, and issue keys are the parts to check) before you rely on it. The touchpoints:
  - **Create issues (Stage 3)** — `gh issue create` in `skills/sdlc/SKILL.md` → the tracker's
    create call (Linear GraphQL / `jira issue create`).
  - **Report status (Stages 3 & 7)** — `gh issue list` / `gh project item-list` in
    `skills/project-status/SKILL.md` → the tracker's list/query (Linear list / Jira JQL). Only the
    fetch line changes; the Now/Next/Blocked grouping stays.
  - **Auto-close on merge (Stage 7)** — the `Closes #N` convention in PRs/commits. This is the
    fiddly one: GitHub closes natively, but Linear/Jira do it through *their* Git integration keyed
    on the issue ID (`ENG-123`, `PROJ-45`) — not a 1:1 command swap. With no such integration,
    close the task **after the human confirms the merge** (the conductor's post-merge step), never
    at Land — an abandoned or rejected PR must not leave the tracker reading done.
  - **Issue shape & branch names** — `.github/ISSUE_TEMPLATE/{epic,task}.md` and `feat/{issue#}-{slug}`
    → the tracker's native issue types/templates and its key (`feat/ENG-123-slug`, which also drives
    the auto-link above).
  - **Auth** — swap the `gh auth` prerequisite for that tracker's CLI auth / API token.

  For **solo/offline**, run "local-only": keep `docs/progress.md` as the tracker itself — otherwise
  **delete `docs/progress.md`**, since the external tracker holds task status.
- **CI enforces the mechanical DoD.** Copy `templates/ci.yml` → `.github/workflows/ci.yml` and
  adjust commands to your stack. "CI green" is then a real Stage-5 (QA) check, not just agent discipline.
- **E2E / Playwright (Stage 5 — QA):** agents run the suite directly via the test runner
  (`npx playwright test`) through shell access — **no MCP required** for authored specs or CI.
  A Playwright **MCP** server is only for *interactive* browser driving during exploratory
  `verify`; it's optional, and `webapp-testing` covers that case too.

## 5. Use skill-creator for the custom skills

Use Anthropic's **`skill-creator`** (the purpose-built authoring skill — it scaffolds valid
frontmatter and can eval/optimize the `description:` that drives triggering) when you edit the
5 custom skills in `skills/`. We hand-wrote starting versions; regenerate/validate with
skill-creator so they stay well-formed and portable.

## 6. Smoke test

Ask the agent: _"Start the sdlc."_ On a **fresh install** it should read `AGENTS.md`, notice
`docs/context.md` still carries the `> STATUS: TEMPLATE` marker, and start the **Stage 0
on-ramp** — interviewing you to fill `docs/context.md` and stopping at the *context filled* gate
(it must NOT advance to Spec while the marker remains). Only once Stage 0 is complete does
_"start the sdlc for a new feature"_ route to Spec (Stage 1) and `brainstorming`.
