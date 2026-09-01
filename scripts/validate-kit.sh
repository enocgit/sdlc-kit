#!/usr/bin/env bash
# Run the critical offline validation suite for the sdlc kit.
set -euo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
unset SKILLS_DIR
export PYTHONDONTWRITEBYTECODE=1
exec python3 "$KIT/scripts/validate-kit.py" "$@"
