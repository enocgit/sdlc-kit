#!/usr/bin/env bash
# Install the sdlc workflow kit into a target project. Non-destructive: never overwrites an
# existing file. Merge-aware: copies file-by-file, so an existing directory (e.g. docs/adr/)
# does not block missing files inside it from being added.
#
# Usage:   ./install.sh [--dry-run] [TARGET_DIR]      (TARGET_DIR default: current directory)
# Env:     SKILLS_DIR=path   where custom skills go (default: TARGET/.agents/skills)
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
case "$KIT" in
*$'\n'* | *$'\r'*)
  echo "Kit path must not contain line breaks" >&2
  exit 2
  ;;
esac
SAFE_INSTALL="$KIT/scripts/install-safe.py"
VENDOR_TOOL="$KIT/scripts/vendor-skills.py"
if ! command -v python3 >/dev/null 2>&1 ||
  ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  echo "Python 3.10 or newer is required" >&2
  exit 2
fi
DRY=0
TARGET_ARG="."
TARGET_SET=0
for a in "$@"; do
  case "$a" in
  --dry-run) DRY=1 ;;
  -h | --help)
    echo "Usage: ./install.sh [--dry-run] [TARGET_DIR]"
    exit 0
    ;;
  -*)
    echo "Unknown option: $a" >&2
    exit 2
    ;;
  *)
    if [ "$TARGET_SET" -eq 1 ]; then
      echo "Only one target directory may be specified" >&2
      exit 2
    fi
    TARGET_ARG="$a"
    TARGET_SET=1
    ;;
  esac
done

vendor_lock_is_held() {
  python3 - "$KIT" <<'PY'
import fcntl
import os
import sys

try:
    descriptor = os.open(sys.argv[1], os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
except OSError:
    raise SystemExit(1)
try:
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit(0)
    raise SystemExit(1)
finally:
    os.close(descriptor)
PY
}

# The environment flag is only a wrapper handoff hint; require its repository lock to be held.
if [ -z "${SDLC_VENDOR_LOCKED:-}" ] || ! vendor_lock_is_held; then
  VENDOR_WRAPPER=install-locked
  [ "$DRY" -eq 1 ] && VENDOR_WRAPPER=preview-locked
  exec python3 "$VENDOR_TOOL" "$VENDOR_WRAPPER" bash "$0" "$@"
fi

# Never trust caller-controlled handoff hashes. Derive copy-time expectations from the lock
# while the vendor-operation lock is held, using the same function as the wrapper.
VENDOR_HASHES="$(python3 "$VENDOR_TOOL" install-hashes)" || {
  echo "Could not derive vendor integrity hashes from the lock" >&2
  exit 1
}
vendor_hash_value() {
  python3 -c 'import json, sys; print(json.loads(sys.argv[1])[sys.argv[2]])' "$VENDOR_HASHES" "$1"
}
SDLC_VENDOR_CONTENT_HASHES="$(vendor_hash_value SDLC_VENDOR_CONTENT_HASHES)"
SDLC_VENDOR_PROVENANCE_HASHES="$(vendor_hash_value SDLC_VENDOR_PROVENANCE_HASHES)"
SDLC_VENDOR_LICENSE_HASHES="$(vendor_hash_value SDLC_VENDOR_LICENSE_HASHES)"
export SDLC_VENDOR_CONTENT_HASHES SDLC_VENDOR_PROVENANCE_HASHES SDLC_VENDOR_LICENSE_HASHES

[ "$DRY" -eq 1 ] && {
  echo "DRY RUN — no files will be written"
  echo "Note: filesystem atomic-rename support is checked during the real install."
  echo
}

# Lexically resolve a path to absolute, collapsing . and .. WITHOUT touching disk — so a dry run
# can predict where `mkdir -p && cd` would land (e.g. `foo/../bar` → .../bar) instead of printing
# an unnormalized path whose no-clobber checks miss the real files.
canonical_path() { # $1 -> physical path, resolving existing symlink aliases
  python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"
}

normalize_path() { # $1 -> absolute normalized path
  local p="$1" part
  local -a parts=() out=()
  case "$p" in
  *$'\n'* | *$'\r'*)
    echo "Paths must not contain line breaks" >&2
    return 2
    ;;
  esac
  case "$p" in /*) ;; *) p="$PWD/$p" ;; esac
  IFS=/ read -r -a parts <<<"$p"
  for part in "${parts[@]}"; do
    case "$part" in
    '' | .) ;;
    ..) [ "${#out[@]}" -gt 0 ] && unset 'out[$(( ${#out[@]} - 1 ))]' ;;
    *) out+=("$part") ;;
    esac
  done
  local joined=""
  for part in "${out[@]}"; do joined="$joined/$part"; done
  printf '%s\n' "${joined:-/}"
}

# Resolve the target identically for dry-run and real run so the preview can't disagree with the
# install. A target that exists but isn't a directory is fatal in both modes (the real run would
# die at `mkdir -p`; the dry run must not pretend it can install there).
TARGET_NORMALIZED="$(normalize_path "$TARGET_ARG")"
# Fail source traversal and line-breaking paths before creating either destination root. The later
# descriptor-safe publication still rechecks each source while copying.
source_traversal_complete=0
while IFS= read -r -d '' source_entry; do
  if [ -z "$source_entry" ]; then
    source_traversal_complete=1
    continue
  fi
  case "$source_entry" in
  *$'\n'* | *$'\r'*)
    echo "Installer source paths must not contain line breaks" >&2
    exit 2
    ;;
  esac
  case "$source_entry" in
  "$KIT/templates/docs"/* | "$KIT/templates/github"/*)
    if [ -L "$source_entry" ] || { [ ! -f "$source_entry" ] && [ ! -d "$source_entry" ]; }; then
      echo "Template trees may contain only real directories and regular files: $source_entry" >&2
      exit 2
    fi
    ;;
  esac
done < <(
  find \
    "$KIT/templates/docs" \
    "$KIT/templates/github" \
    "$KIT/skills" \
    "$KIT/vendor/skills" \
    -print0 && printf '\0'
)
if [ "$source_traversal_complete" -ne 1 ]; then
  echo "Could not traverse installer source trees" >&2
  exit 2
fi
for fixed_source in \
  "$KIT/templates/AGENTS.md" \
  "$KIT/templates/CLAUDE.md" \
  "$KIT/required-skills.yml"; do
  python3 "$SAFE_INSTALL" source "$fixed_source" >/dev/null
done
if [ -L "$TARGET_NORMALIZED" ]; then
  echo "Target must not be a symlink: $TARGET_ARG" >&2
  exit 2
fi
if [ -e "$TARGET_ARG" ] && [ ! -d "$TARGET_ARG" ]; then
  echo "Target exists but is not a directory: $TARGET_ARG" >&2
  exit 2
fi
target_root_args=(root "$TARGET_NORMALIZED")
[ "$DRY" -eq 1 ] || target_root_args+=(--create)
python3 "$SAFE_INSTALL" "${target_root_args[@]}" >/dev/null
target_check_args=(check "$TARGET_NORMALIZED")
[ "$DRY" -eq 1 ] || target_check_args+=(--write-probe)
python3 "$SAFE_INSTALL" "${target_check_args[@]}" >/dev/null
TARGET="$TARGET_NORMALIZED"

# Skills default to .agents/skills; a RELATIVE SKILLS_DIR override is resolved against the TARGET
# project, not the installer's CWD, so `SKILLS_DIR=.claude/skills` lands inside the project (not in
# the kit checkout) — see INSTALL.md. An explicit override is an intentional external write root;
# the default remains contained by TARGET.
if [ "${SKILLS_DIR+x}" = x ]; then
  SKILLS_DIR_EXPLICIT=1
else
  SKILLS_DIR_EXPLICIT=0
fi
SKILLS_DIR="${SKILLS_DIR:-$TARGET/.agents/skills}"
case "$SKILLS_DIR" in
/*) SKILLS_DIR="$(normalize_path "$SKILLS_DIR")" ;;
*)
  SKILLS_DIR="$(normalize_path "$TARGET/$SKILLS_DIR")"
  case "$SKILLS_DIR" in
  "$TARGET" | "$TARGET"/*) ;;
  *)
    echo "Relative SKILLS_DIR escapes the target project: $SKILLS_DIR" >&2
    exit 2
    ;;
  esac
  ;;
esac
case "$SKILLS_DIR" in
"$TARGET" | "$TARGET"/*) SKILL_WRITE_ROOT="$TARGET" ;;
*)
  if [ "$SKILLS_DIR_EXPLICIT" -eq 1 ]; then
    SKILL_WRITE_ROOT="$SKILLS_DIR"
  else
    SKILL_WRITE_ROOT="$TARGET"
  fi
  ;;
esac
skills_root_args=(root "$SKILLS_DIR")
[ "$DRY" -eq 1 ] || skills_root_args+=(--create)
python3 "$SAFE_INSTALL" "${skills_root_args[@]}" >/dev/null
skills_check_args=(check "$SKILLS_DIR")
[ "$DRY" -eq 1 ] || skills_check_args+=(--write-probe)
python3 "$SAFE_INSTALL" "${skills_check_args[@]}" >/dev/null

echo "Kit:    $KIT"
echo "Target: $TARGET"
echo "Skills: $SKILLS_DIR"
echo

ADDED=0
SKIPPED=0
SKIPPED_LIST=()

ensure_safe_parent() { # allowed-root destination
  local root="$1" destination="$2" parent relative current part
  local -a parts=()
  case "$root$destination" in
  *$'\n'* | *$'\r'*)
    echo "Paths must not contain line breaks" >&2
    return 2
    ;;
  esac
  [ "$root" = "/" ] || root="${root%/}"
  parent="$(dirname "$destination")"
  if [ "$root" = "/" ]; then
    relative="${parent#/}"
    current=""
  else
    case "$parent" in
    "$root") return 0 ;;
    "$root"/*)
      relative="${parent#"$root"/}"
      current="$root"
      ;;
    *)
      echo "Refusing write outside allowed root: $destination" >&2
      return 1
      ;;
    esac
  fi
  IFS=/ read -r -a parts <<<"$relative"
  for part in "${parts[@]}"; do
    [ -n "$part" ] || continue
    current="$current/$part"
    if [ -L "$current" ]; then
      echo "Refusing write through symlinked directory: $current" >&2
      return 1
    fi
    if [ -e "$current" ] && [ ! -d "$current" ]; then
      echo "Refusing write through non-directory path: $current" >&2
      return 1
    fi
  done
}

preflight_tree() { # allowed-root srcdir dstdir
  local root="$1" srcdir="${2%/}" dstdir="${3%/}" f rel traversal_complete=0
  [ -d "$srcdir" ] || return 0
  while IFS= read -r -d '' f; do
    if [ -z "$f" ]; then
      traversal_complete=1
      continue
    fi
    if [ -L "$f" ] || { [ ! -f "$f" ] && [ ! -d "$f" ]; }; then
      echo "Template trees may contain only real directories and regular files: $f" >&2
      return 1
    fi
    [ -d "$f" ] && continue
    rel="${f#"$srcdir"/}"
    ensure_safe_parent "$root" "$dstdir/$rel"
  done < <(find "$srcdir" -print0 && printf '\0')
  if [ "$traversal_complete" -ne 1 ]; then
    echo "Could not traverse source tree: $srcdir" >&2
    return 1
  fi
}

skip_file() { # rel
  local rel="$1"
  SKIPPED=$((SKIPPED + 1))
  SKIPPED_LIST+=("$rel")
  echo "  skip (exists): $rel"
}

copy_file() { # src dst — descriptor-relative, atomic no-clobber publication
  local src="$1" dst="$2" rel="${2#"$TARGET"/}" result
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    skip_file "$rel"
    return 0
  fi
  ensure_safe_parent "$TARGET" "$dst"
  if [ "$DRY" -eq 1 ]; then
    ADDED=$((ADDED + 1))
    echo "  + $rel"
    return 0
  fi

  result="$(python3 "$SAFE_INSTALL" file "$TARGET" "$src" "$dst")"
  if [ "$result" = "added" ]; then
    ADDED=$((ADDED + 1))
    echo "  + $rel"
  elif [ "$result" = "exists" ]; then
    skip_file "$rel"
  else
    echo "Unexpected safe installer result for $dst: $result" >&2
    return 1
  fi
}

copy_tree() { # srcdir dstdir — recursive, file-level no-clobber
  local srcdir="${1%/}" dstdir="${2%/}" f rel traversal_complete=0
  [ -d "$srcdir" ] || return 0
  while IFS= read -r -d '' f; do
    if [ -z "$f" ]; then
      traversal_complete=1
      continue
    fi
    if [ -L "$f" ] || { [ ! -f "$f" ] && [ ! -d "$f" ]; }; then
      echo "Template trees may contain only real directories and regular files: $f" >&2
      return 1
    fi
    [ -d "$f" ] && continue
    rel="${f#"$srcdir"/}"
    copy_file "$f" "$dstdir/$rel"
  done < <(find "$srcdir" -print0 && printf '\0')
  if [ "$traversal_complete" -ne 1 ]; then
    echo "Could not traverse source tree: $srcdir" >&2
    return 1
  fi
}

skip_skill() { # rel
  local rel="$1"
  SKIPPED=$((SKIPPED + 1))
  SKIPPED_LIST+=("$rel/")
  echo "  skip (exists): $rel/"
}

copy_skill() { # srcdir dstdir [vendored-skill-name] — descriptor-relative no-clobber
  local srcdir="${1%/}" dstdir="${2%/}" metadata="${3:-}" rel="${2#"$TARGET"/}" result
  local expected_hash expected_provenance_hash expected_license_hash
  if [ -e "$dstdir" ] || [ -L "$dstdir" ]; then
    skip_skill "$rel"
    return 0
  fi
  ensure_safe_parent "$SKILL_WRITE_ROOT" "$dstdir"
  if [ "$DRY" -eq 1 ]; then
    ADDED=$((ADDED + 1))
    echo "  + $rel/"
    return 0
  fi
  if [ -n "$metadata" ]; then
    expected_hash="$(python3 -c 'import json, os, sys; print(json.loads(os.environ["SDLC_VENDOR_CONTENT_HASHES"])[sys.argv[1]])' "$metadata")"
    expected_provenance_hash="$(python3 -c 'import json, os, sys; print(json.loads(os.environ["SDLC_VENDOR_PROVENANCE_HASHES"])[sys.argv[1]])' "$metadata")"
    expected_license_hash="$(python3 -c 'import json, os, sys; print(json.loads(os.environ["SDLC_VENDOR_LICENSE_HASHES"])[sys.argv[1]])' "$metadata")"
    result="$(python3 "$SAFE_INSTALL" tree "$SKILL_WRITE_ROOT" "$srcdir" "$dstdir" \
      --provenance "$KIT/vendor/provenance/$metadata.json" \
      --license "$KIT/vendor/licenses/$metadata.txt" \
      --expected-content-sha256 "$expected_hash" \
      --expected-provenance-sha256 "$expected_provenance_hash" \
      --expected-license-sha256 "$expected_license_hash")"
  else
    result="$(python3 "$SAFE_INSTALL" tree "$SKILL_WRITE_ROOT" "$srcdir" "$dstdir")"
  fi
  if [ "$result" = "added" ]; then
    ADDED=$((ADDED + 1))
    echo "  + $rel/"
  elif [ "$result" = "exists" ]; then
    skip_skill "$rel"
  else
    echo "Unexpected safe installer result for $dstdir: $result" >&2
    return 1
  fi
}

clean_template_parents() { # source tree destination tree — clean only parents that receive files
  local srcdir="${1%/}" dstdir="${2%/}" source_file rel parent_rel destination_dir
  while IFS= read -r -d '' source_file; do
    rel="${source_file#"$srcdir"/}"
    if [[ "$rel" == */* ]]; then
      parent_rel="${rel%/*}"
      destination_dir="$dstdir/$parent_rel"
    else
      destination_dir="$dstdir"
    fi
    python3 "$SAFE_INSTALL" clean "$TARGET" "$destination_dir" >/dev/null
  done < <(find "$srcdir" -type f -print0)
}

# Validate every destination parent before publishing anything, so dry-run and real installs reject
# the same path conflicts and a late conflict cannot leave a partial install.
ensure_safe_parent "$TARGET" "$TARGET/AGENTS.md"
ensure_safe_parent "$TARGET" "$TARGET/CLAUDE.md"
ensure_safe_parent "$TARGET" "$TARGET/required-skills.yml"
preflight_tree "$TARGET" "$KIT/templates/docs" "$TARGET/docs"
preflight_tree "$TARGET" "$KIT/templates/github" "$TARGET/.github"
for d in "$KIT"/skills/*/; do
  ensure_safe_parent "$SKILL_WRITE_ROOT" "$SKILLS_DIR/$(basename "$d")"
done
for d in "$KIT"/vendor/skills/*/; do
  ensure_safe_parent "$SKILL_WRITE_ROOT" "$SKILLS_DIR/$(basename "$d")"
done

# Clean interrupted-run staging in every publication parent, even when all destinations already
# exist and the file/skill copy helpers will skip them. The marker separately cleans TARGET's root.
if [ "$DRY" -eq 0 ]; then
  clean_template_parents "$KIT/templates/docs" "$TARGET/docs"
  clean_template_parents "$KIT/templates/github" "$TARGET/.github"
  python3 "$SAFE_INSTALL" clean "$SKILL_WRITE_ROOT" "$SKILLS_DIR" >/dev/null
fi

# Operating manual + one-line CLAUDE.md pointer
copy_file "$KIT/templates/AGENTS.md" "$TARGET/AGENTS.md"
copy_file "$KIT/templates/CLAUDE.md" "$TARGET/CLAUDE.md"

# Skills manifest — installed skills (conductor fallbacks) reference it, so it ships too
copy_file "$KIT/required-skills.yml" "$TARGET/required-skills.yml"

# Project templates merge file-by-file. Skills install as complete directories so an existing local
# version cannot become a mixture of two snapshots.
copy_tree "$KIT/templates/docs" "$TARGET/docs"
copy_tree "$KIT/templates/github" "$TARGET/.github"
for d in "$KIT"/skills/*/; do
  copy_skill "$d" "$SKILLS_DIR/$(basename "$d")"
done
for d in "$KIT"/vendor/skills/*/; do
  name="$(basename "$d")"
  copy_skill "$d" "$SKILLS_DIR/$name" "$name"
done

# Kit version marker — the one managed exception to no-clobber: an existing marker for a
# different release is replaced, so re-running after an upgrade reports the new version.
if awk '
  /^## \[Unreleased\]$/ { in_unreleased = 1; next }
  /^## \[/ { if (in_unreleased) exit }
  in_unreleased && $0 !~ /^[[:space:]]*$/ && $0 !~ /^### / { found = 1; exit }
  END { exit(found ? 0 : 1) }
' "$KIT/CHANGELOG.md"; then
  KIT_VERSION="unreleased"
else
  KIT_VERSION="$(sed -n 's/^## \[\([0-9][0-9A-Za-z.]*\)\] - .*/\1/p' "$KIT/CHANGELOG.md" | head -1)"
  KIT_VERSION="${KIT_VERSION:-unreleased}"
fi
if [ "$DRY" -eq 1 ]; then
  echo "  ~ .sdlc-kit-version -> $KIT_VERSION (dry run)"
else
  MARKER_RESULT="$(python3 "$SAFE_INSTALL" version "$TARGET" "$KIT_VERSION")"
  echo "  marker: .sdlc-kit-version $KIT_VERSION ($MARKER_RESULT)"
fi

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
echo "Next: ask your agent to \"start the sdlc\"."
