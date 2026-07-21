#!/usr/bin/env bash
# Validate the sdlc kit itself (for maintainers / CI of this repo).
# Checks: install.sh syntax, a real smoke install to a temp dir (expected files DERIVED from the
# kit tree, so new/renamed templates and skills are covered automatically), kit tree ↔
# scripts/kit-manifest.txt in both directions (so deleting a shipped file fails), --dry-run
# writes nothing, merge-awareness, skill frontmatter, no HTML-breaking placeholders,
# required-skills.yml parses, and every `kind: local` manifest path exists.
set -uo pipefail

# The kit's install target-skills go to .agents/skills by default; if the maintainer exports
# SKILLS_DIR, every install.sh invocation below would inherit it — writing kit skills outside the
# mktemp sandbox (never cleaned) and then failing the .agents/skills expectations on a healthy kit.
# The validator owns its own expectations, so it always tests the default layout.
unset SKILLS_DIR

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FAIL=0
pass() { echo "  ok   $1"; }
fail() { echo "  FAIL $1"; FAIL=1; }

echo "Validating kit at $KIT"

# 1. install.sh syntax
echo "[1] install.sh syntax"
bash -n "$KIT/install.sh" && pass "bash -n install.sh" || fail "install.sh has syntax errors"

# 2. smoke install to a temp dir; expected files are DERIVED from the kit tree so a deleted or
#    renamed template/skill fails here instead of silently vanishing from installs
echo "[2] smoke install"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
if bash "$KIT/install.sh" "$TMP" >/dev/null 2>&1; then
  MISS=0
  check_installed() { [ -e "$TMP/$1" ] || { fail "missing after install: $1"; MISS=1; }; }
  # fixed outputs
  for expected in AGENTS.md CLAUDE.md required-skills.yml .github/workflows/ci.yml; do
    check_installed "$expected"
  done
  # every file under templates/docs must land in docs/
  while IFS= read -r -d '' f; do
    check_installed "docs/${f#"$KIT/templates/docs/"}"
  done < <(find "$KIT/templates/docs" -type f -print0)
  # every file under templates/github must land in .github/
  while IFS= read -r -d '' f; do
    check_installed ".github/${f#"$KIT/templates/github/"}"
  done < <(find "$KIT/templates/github" -type f -print0)
  # every kit skill must land in the skills dir
  for d in "$KIT"/skills/*/; do
    check_installed ".agents/skills/$(basename "$d")/SKILL.md"
  done
  [ "$MISS" -eq 0 ] && pass "all kit templates + skills landed ($(find "$TMP" -type f | wc -l) files)"
else
  fail "install.sh exited non-zero"
fi

# 2b. shipped-file inventory: the kit tree must match the checked-in manifest in BOTH directions,
#     so deleting/renaming a shipped file fails until scripts/kit-manifest.txt is deliberately
#     updated (regenerate: find templates skills -type f | sort > scripts/kit-manifest.txt)
echo "[2b] shipped-file inventory vs kit-manifest.txt"
if diff <(cd "$KIT" && find templates skills -type f | sort) "$KIT/scripts/kit-manifest.txt" >/dev/null 2>&1; then
  pass "kit tree matches manifest ($(wc -l < "$KIT/scripts/kit-manifest.txt") shipped files)"
else
  fail "kit tree ≠ scripts/kit-manifest.txt — if the change is intentional, regenerate the manifest:"
  diff <(cd "$KIT" && find templates skills -type f | sort) "$KIT/scripts/kit-manifest.txt" | sed 's/^/      /'
fi

# 2c. --dry-run must not write anything (including the target directory itself)
echo "[2c] dry run writes nothing"
DRYTGT="$(mktemp -d)/does/not/exist"
if bash "$KIT/install.sh" --dry-run "$DRYTGT" >/dev/null 2>&1 && [ ! -e "$DRYTGT" ]; then
  pass "--dry-run exited clean and created no target directory"
else
  fail "--dry-run either errored or wrote to disk ($DRYTGT)"
fi
rm -rf "${DRYTGT%/does/not/exist}"

# 3. merge-awareness: a pre-existing docs/adr/ must not block adding TEMPLATE.md inside it
echo "[3] merge-aware install"
TMP2="$(mktemp -d)"; mkdir -p "$TMP2/docs/adr"; echo "existing" > "$TMP2/docs/adr/0001-mine.md"
bash "$KIT/install.sh" "$TMP2" >/dev/null 2>&1
[ -e "$TMP2/docs/adr/TEMPLATE.md" ] && pass "added TEMPLATE.md into pre-existing docs/adr/" \
  || fail "file-level no-clobber failed (docs/adr existed, TEMPLATE.md not added)"
[ "$(cat "$TMP2/docs/adr/0001-mine.md")" = "existing" ] && pass "preserved existing adr file" \
  || fail "clobbered an existing file"
rm -rf "$TMP2"

# 4. skill frontmatter: name matches dir + description present
echo "[4] skill frontmatter"
for f in "$KIT"/skills/*/SKILL.md; do
  dir="$(basename "$(dirname "$f")")"
  name="$(awk -F': *' '/^name:/{print $2; exit}' "$f")"
  [ "$name" = "$dir" ] && pass "name=$name matches dir" || fail "name '$name' != dir '$dir'"
  grep -q '^description:' "$f" && pass "$dir has description" || fail "$dir missing description"
done

# 5. no HTML-breaking <tag> placeholders in templates (use {placeholder} instead)
echo "[5] placeholder hygiene"
if grep -rnE '<[A-Za-z][^<>]*>' "$KIT/templates" "$KIT/AGENTS.md" "$KIT/skills" "$KIT/README.md" >/dev/null 2>&1; then
  fail "found <tag>-style placeholders (breaks markdown preview) — use {placeholder}"
  grep -rnE '<[A-Za-z][^<>]*>' "$KIT/templates" "$KIT/AGENTS.md" "$KIT/skills" "$KIT/README.md" | sed 's/^/      /'
else
  pass "no HTML-breaking placeholders"
fi

# 6. required-skills.yml parses (if a YAML parser is available)
echo "[6] required-skills.yml"
if command -v python3 >/dev/null 2>&1; then
  if python3 -c "import yaml,sys; yaml.safe_load(open('$KIT/required-skills.yml'))" 2>/dev/null; then
    pass "required-skills.yml is valid YAML"
  else
    python3 -c "import yaml" 2>/dev/null && fail "required-skills.yml is invalid YAML" \
      || echo "  skip (pyyaml not installed)"
  fi
else
  echo "  skip (python3 not available)"
fi

# 7. every `kind: local` path in required-skills.yml must exist in the kit (and vice versa: every
#    kit skill must be declared). Parse via PyYAML so a valid reformat (block style, reordered keys)
#    can't silently disable the check the way a grep/sed pattern coupled to one-line flow style does.
echo "[7] manifest ↔ skills/ agreement"
if command -v python3 >/dev/null 2>&1 && python3 -c "import yaml" 2>/dev/null; then
  LOCAL_TSV="$(python3 - "$KIT/required-skills.yml" <<'PY'
import sys, yaml
data = yaml.safe_load(open(sys.argv[1])) or {}
for s in data.get("skills", []):
    if isinstance(s, dict) and s.get("kind") == "local":
        print(f"{s.get('name','')}\t{s.get('path','')}")
PY
)"
  # forward: every declared local path resolves to a real skill
  while IFS=$'\t' read -r n p; do
    [ -n "$p" ] || continue
    [ -f "$KIT/$p/SKILL.md" ] && pass "manifest path exists: $p" || fail "manifest points at missing skill: $p"
  done <<< "$LOCAL_TSV"
  # reverse: every kit skill is declared local in the manifest
  DECLARED="$(printf '%s\n' "$LOCAL_TSV" | cut -f1)"
  for d in "$KIT"/skills/*/; do
    n="$(basename "$d")"
    printf '%s\n' "$DECLARED" | grep -qx "$n" \
      && pass "skill declared in manifest: $n" || fail "skill not in required-skills.yml: $n"
  done
else
  echo "  skip (python3 + pyyaml required for a reformat-proof manifest parse)"
fi

echo "[8] Stage 7 closing-keyword scoping"
# `Closes #N` is GitHub-only. Every Stage 7 pipeline row must scope it, or the summaries drift
# back to implying it works on Linear/Jira/local-only (where it closes an unrelated issue).
for f in AGENTS.md README.md CHEATSHEET.md skills/sdlc/SKILL.md; do
  row="$(grep -m1 '^| 7 ' "$KIT/$f" || true)"
  if [ -z "$row" ]; then
    fail "$f: no Stage 7 pipeline row found"
  elif printf '%s' "$row" | grep -q 'Closes #' && ! printf '%s' "$row" | grep -q 'GitHub'; then
    fail "$f: Stage 7 row mentions 'Closes #' without scoping it to GitHub"
  else
    pass "$f: Stage 7 closing keyword scoped"
  fi
done
# The canonical statement must exist for the pointers to resolve.
grep -q '^## Task completion by tracker' "$KIT/skills/sdlc/SKILL.md" \
  && pass "canonical 'Task completion by tracker' section present" \
  || fail "skills/sdlc/SKILL.md: canonical 'Task completion by tracker' section missing"

echo "[9] Stage 7 capability separation"
for f in AGENTS.md README.md skills/sdlc/SKILL.md; do
  row="$(grep -m1 '^| 7 ' "$KIT/$f" || true)"
  if printf '%s' "$row" | grep -Eq 'if a remote exists|iff a remote exists'; then
    pass "$f: Stage 7 push is conditional on a remote"
  else
    fail "$f: Stage 7 must not require a push when no remote exists"
  fi
done
for mode in \
  '**PR workflow available**' \
  '**No PR workflow, CI workflow available**' \
  '**No PR or CI workflow**'; do
  grep -Fq "$mode" "$KIT/skills/sdlc/SKILL.md" \
    && pass "skills/sdlc/SKILL.md: documents $mode" \
    || fail "skills/sdlc/SKILL.md: missing independent landing mode $mode"
done
if grep -Fq '`project-status` (reads only)' "$KIT/skills/sdlc/SKILL.md"; then
  fail "skills/sdlc/SKILL.md: Stage 7 incorrectly makes local-only tracker handling read-only"
else
  pass "skills/sdlc/SKILL.md: local-only tracker write is not suppressed"
fi
push_prereq="$(grep -m1 'git push.*must work non-interactively' "$KIT/INSTALL.md" || true)"
if printf '%s' "$push_prereq" | grep -q 'projects with a remote'; then
  pass "INSTALL.md: non-interactive push prerequisite is conditional on a remote"
else
  fail "INSTALL.md: non-interactive push must not be required for no-remote projects"
fi

echo "[10] onboarding documentation boundaries"
grep -Fq '**Gate:** context filled.' "$KIT/EXAMPLE.md" \
  && pass "EXAMPLE.md: Stage 0a context gate preserved" \
  || fail "EXAMPLE.md: Stage 0a must stop at the context-filled gate before foundation"
if grep -Fq 'Install only the **community** rows with `npx skills add`.' "$KIT/INSTALL.md" \
  && grep -Fq 'For **runtime-native** rows' "$KIT/INSTALL.md"; then
  pass "INSTALL.md: registry and runtime-native skills distinguished"
else
  fail "INSTALL.md: registry installation must be limited to community skills"
fi
grep -Fq 'npx skills add obra/superpowers --skill writing-plans' "$KIT/INSTALL.md" \
  && pass "INSTALL.md: community install example uses --skill selector" \
  || fail "INSTALL.md: community install example must use the supported --skill selector"
if grep -Fq 'fresh projects stop at six human approval gates' "$KIT/README.md" \
  && grep -Fq 'Fresh projects have six hard gates' "$KIT/CHEATSHEET.md"; then
  pass "README/CHEATSHEET: bootstrap context gate included in gate count"
else
  fail "README/CHEATSHEET: fresh-project onboarding must count all six gates"
fi
if grep -Fq 'bootstrap: context filled' "$KIT/AGENTS.md" \
  && grep -Fq 'adopt: approve reconstructed foundation' "$KIT/AGENTS.md"; then
  pass "AGENTS.md: Stage 0 gates distinguish bootstrap from adoption"
else
  fail "AGENTS.md: Stage 0 must use two bootstrap gates but one adoption gate"
fi
for f in skills/sdlc/SKILL.md INSTALL.md CHEATSHEET.md; do
  if grep -Fq 'sdlc {chosen direction}' "$KIT/$f"; then
    pass "$f: improve-next handoff returns through sdlc"
  else
    fail "$f: improve next must return the chosen direction through sdlc"
  fi
done
for f in README.md CHEATSHEET.md; do
  grep -Fq '`address-review`' "$KIT/$f" \
    && pass "$f: standalone address-review skill is discoverable" \
    || fail "$f: standalone address-review skill must be named"
done

echo
[ "$FAIL" -eq 0 ] && echo "ALL CHECKS PASSED" || echo "SOME CHECKS FAILED"
exit "$FAIL"
