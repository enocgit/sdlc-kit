# Contracts

## Authoritative artifacts

| Contract | Source of truth | Consumers |
| --- | --- | --- |
| Installed kit mapping | `install.sh` | Target repositories |
| Maintained template/skill inventory | `scripts/kit-manifest.txt` | Validation and maintainers |
| Required skill metadata | `required-skills.yml`, validated by `scripts/validate-required-skills.py` | Conductor, documentation, maintainers |
| Vendored snapshot identity | `vendor/skills.lock.json`, `vendor/provenance/*.json` | Vendor tooling and installer |
| Installed vendor metadata | `.sdlc-vendor/provenance.json`, `.sdlc-vendor/LICENSE.txt` | `verify-installed` and adopters |
| Pipeline behavior | `templates/AGENTS.md`, `skills/sdlc/SKILL.md` | Installed coding agents |

## Change rules

- Change a schema and its validator in the same patch.
- Keep manifest, lock, provenance, documentation, and generated installation commands consistent.
- Keep `vendor/skills/**` byte-for-byte equal to the pinned upstream tree.
- Treat installer command-line arguments and environment continuations as internal contracts between
  `install.sh`, `scripts/vendor-skills.py`, and `scripts/install-safe.py`.
- Record a compatibility decision before changing a shipped public field, command, or destination.
