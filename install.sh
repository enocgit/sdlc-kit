#!/usr/bin/env bash
# Install the sdlc workflow kit into a target project. Non-destructive: never overwrites an
# existing file. Merge-aware: copies file-by-file, so an existing directory (e.g. docs/adr/)
# does not block missing files inside it from being added.
#
# Usage:   ./install.sh [--dry-run] [TARGET_DIR]      (TARGET_DIR default: current directory)
# Env:     SKILLS_DIR=path   where custom skills go (default: TARGET/.claude/skills)
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY=0
TARGET_ARG="."
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    -h|--help) echo "Usage: ./install.sh [--dry-run] [TARGET_DIR]"; exit 0 ;;
    -*) echo "Unknown option: $a" >&2; exit 2 ;;
    *) TARGET_ARG="$a" ;;
  esac
done

[ "$DRY" -eq 1 ] && { echo "DRY RUN — no files will be written"; echo; }

# Lexically resolve a path to absolute, collapsing . and .. WITHOUT touching disk — so a dry run
# can predict where `mkdir -p && cd` would land (e.g. `foo/../bar` → .../bar) instead of printing
# an unnormalized path whose no-clobber checks miss the real files.
normalize_path() { # $1 -> absolute normalized path
  local p="$1" part; local -a out=()
  case "$p" in /*) ;; *) p="$PWD/$p" ;; esac
  local IFS=/
  for part in $p; do
    case "$part" in
      ''|.) ;;
      ..) [ "${#out[@]}" -gt 0 ] && unset 'out[$(( ${#out[@]} - 1 ))]' ;;
      *)  out+=("$part") ;;
    esac
  done
  local joined=""; for part in "${out[@]}"; do joined="$joined/$part"; done
  printf '%s\n' "${joined:-/}"
}

# Resolve the target identically for dry-run and real run so the preview can't disagree with the
# install. A target that exists but isn't a directory is fatal in both modes (the real run would
# die at `mkdir -p`; the dry run must not pretend it can install there).
if [ -e "$TARGET_ARG" ] && [ ! -d "$TARGET_ARG" ]; then
  echo "Target exists but is not a directory: $TARGET_ARG" >&2; exit 2
fi
[ "$DRY" -eq 0 ] && mkdir -p "$TARGET_ARG"
if [ -d "$TARGET_ARG" ]; then
  TARGET="$(cd "$TARGET_ARG" && pwd)"
else
  # dry run against a not-yet-existing dir — resolve it lexically, create nothing
  TARGET="$(normalize_path "$TARGET_ARG")"
fi

# Skills default to .claude/skills; a RELATIVE SKILLS_DIR override is resolved against the TARGET
# project, not the installer's CWD, so `SKILLS_DIR=.agents/skills` lands inside the project (not in
# the kit checkout) — see INSTALL.md.
SKILLS_DIR="${SKILLS_DIR:-$TARGET/.claude/skills}"
case "$SKILLS_DIR" in
  /*) ;;
  *)  SKILLS_DIR="$TARGET/$SKILLS_DIR" ;;
esac

echo "Kit:    $KIT"
echo "Target: $TARGET"
echo "Skills: $SKILLS_DIR"
echo

ADDED=0
SKIPPED=0
SKIPPED_LIST=()

copy_file() { # src dst
  local src="$1" dst="$2" rel="${2#"$TARGET"/}"
  if [ -e "$dst" ]; then
    SKIPPED=$((SKIPPED + 1)); SKIPPED_LIST+=("$rel"); echo "  skip (exists): $rel"
  else
    if [ "$DRY" -eq 0 ]; then mkdir -p "$(dirname "$dst")"; cp "$src" "$dst"; fi
    ADDED=$((ADDED + 1)); echo "  + $rel"
  fi
}

copy_tree() { # srcdir dstdir — recursive, file-level no-clobber
  local srcdir="${1%/}" dstdir="${2%/}" f rel
  [ -d "$srcdir" ] || return 0
  while IFS= read -r -d '' f; do
    rel="${f#"$srcdir"/}"
    copy_file "$f" "$dstdir/$rel"
  done < <(find "$srcdir" -type f -print0)
}

# Operating manual + one-line CLAUDE.md pointer
copy_file "$KIT/AGENTS.md" "$TARGET/AGENTS.md"
if [ ! -e "$TARGET/CLAUDE.md" ]; then
  [ "$DRY" -eq 0 ] && echo "See AGENTS.md for how we work on this project." > "$TARGET/CLAUDE.md"
  ADDED=$((ADDED + 1)); echo "  + CLAUDE.md"
else
  SKIPPED=$((SKIPPED + 1)); SKIPPED_LIST+=("CLAUDE.md"); echo "  skip (exists): CLAUDE.md"
fi

# Skills manifest — installed skills (conductor fallbacks) reference it, so it ships too
copy_file "$KIT/required-skills.yml" "$TARGET/required-skills.yml"

# docs/, CI, GitHub templates, and custom skills (all file-level no-clobber)
copy_tree "$KIT/templates/docs" "$TARGET/docs"
copy_file "$KIT/templates/ci.yml" "$TARGET/.github/workflows/ci.yml"
copy_tree "$KIT/templates/github" "$TARGET/.github"
for d in "$KIT"/skills/*/; do
  copy_tree "$d" "$SKILLS_DIR/$(basename "$d")"
done

# Summary / conflict report
echo
echo "Summary: $ADDED added, $SKIPPED skipped (already existed)."
if [ "$SKIPPED" -gt 0 ]; then
  echo "Existing files were left untouched. Review them against the kit versions and merge by"
  echo "hand if you want the kit's content:"
  for s in "${SKIPPED_LIST[@]}"; do
    if [ "$s" = "CLAUDE.md" ]; then
      echo "  - $s  (tip: add a one-line pointer to AGENTS.md so agents find the manual)"
    else
      echo "  - $s"
    fi
  done
fi
echo
echo "Next: install the community skills in $KIT/INSTALL.md (see required-skills.yml), then ask"
echo "your agent to \"start the sdlc\". (Stage 0 isn't done until docs/context.md is filled.)"
