# Test strategy

## Scope

This repository ships a Bash installer, Python safety and vendoring tools, YAML manifests, Markdown
workflow artifacts, and pinned third-party snapshots. The canonical Definition of Ready and
Definition of Done remain in [`AGENTS.md`](../AGENTS.md).

## Verification

| Layer | Tool | Required evidence |
| --- | --- | --- |
| Critical installer integration | `./scripts/validate-kit.sh` | Offline clean and dry-run installs, restrictive umask, no-clobber race, recovery and quarantine, containment, source-entry rejection, and installed-integrity checks |
| Provenance | `python3 scripts/vendor-skills.py verify` | Snapshot, license, provenance, and lock agreement |
| Manifest schema | `python3 scripts/validate-required-skills.py required-skills.yml` | Strict YAML and kind-specific fields |
| Syntax and static checks | `bash -n`, `python3 -m py_compile`, LSP, `git diff --check` | Changed Bash, Python, Markdown, and YAML are clean |

Start behavioral fixes with a failing regression in the focused Python validation suite, then make the
smallest implementation change that passes it. The default validator covers release-critical runtime
invariants only; prose, routing, and duplicated parser checks belong in review, not this gate.
Documentation-only changes need the relevant validator check
and link or rendering inspection. Networked `sync` and `update` tests require an explicit maintenance
run; normal validation and installation stay offline.

## Release bar

- Run `./scripts/validate-kit.sh` under the default umask and `umask 077`.
- Verify vendored snapshots and the required-skills manifest independently.
- Confirm `vendor/skills/**` and `vendor/licenses/**` are unchanged unless the task is an approved
  snapshot refresh or snapshot removal performed with `scripts/vendor-skills.py remove`; all
  remaining pinned snapshots must stay byte-identical.
- Run runtime observation through a temporary installation for installer-affecting changes.
