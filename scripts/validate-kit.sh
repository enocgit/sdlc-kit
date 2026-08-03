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
  if python3 - "$KIT/required-skills.yml" <<'PY'
import re
import sys
import yaml

data = yaml.safe_load(open(sys.argv[1])) or {}
skill = next(
    (item for item in data.get("skills", [])
     if isinstance(item, dict) and item.get("name") == "test-driven-development"),
    {},
)
stages = {part for part in re.split(r"[\s,]+", str(skill.get("stage", ""))) if part}
note = str(skill.get("note", ""))
raise SystemExit(
    0
    if stages == {"none"}
    and "optional strict mode" in note
    and "auto-trigger" in note
    else 1
)
PY
  then
    pass "strict test-driven-development is an explicit optional mode"
  else
    fail "test-driven-development must be optional because its upstream skill auto-triggers broadly"
  fi
  stage_four_row="$(grep -m1 '^| 4 Implement ' "$KIT/skills/sdlc/SKILL.md" || true)"
  stage_five_row="$(grep -m1 '^| 5 QA ' "$KIT/skills/sdlc/SKILL.md" || true)"
  if ! printf '%s' "$stage_four_row" | grep -Fq '`test-driven-development`' \
    && ! printf '%s' "$stage_five_row" | grep -Fq '`test-driven-development`'; then
    pass "conductor does not force the optional strict TDD skill"
  else
    fail "conductor must not force the optional strict TDD skill in Stage 4 or 5"
  fi
  if python3 - "$KIT/required-skills.yml" <<'PY'
import sys
import yaml

data = yaml.safe_load(open(sys.argv[1])) or {}
names = {
    item.get("name")
    for item in data.get("skills", [])
    if isinstance(item, dict)
}
raise SystemExit(0 if "grilling" in names and "grill-me" not in names else 1)
PY
  then
    pass "Stage 1 declares the executable grilling skill directly"
  else
    fail "Stage 1 must declare grilling directly, not the grill-me wrapper"
  fi
  stage_one_row="$(grep -m1 '^| 1 Spec ' "$KIT/skills/sdlc/SKILL.md" || true)"
  if printf '%s' "$stage_one_row" | grep -Fq '`grilling`' \
    && ! printf '%s' "$stage_one_row" | grep -Fq '`grill-me`'; then
    pass "Stage 1 conductor invokes grilling directly"
  else
    fail "Stage 1 conductor must invoke grilling directly, not the grill-me wrapper"
  fi
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
for f in README.md CHEATSHEET.md; do
  stage_zero_row="$(grep -m1 '^| 0 ' "$KIT/$f" || true)"
  if printf '%s' "$stage_zero_row" | grep -Fq 'bootstrap' \
    && printf '%s' "$stage_zero_row" | grep -Fq 'adopt'; then
    pass "$f: Stage 0 distinguishes bootstrap from adoption"
  else
    fail "$f: Stage 0 row must distinguish bootstrap from adoption"
  fi
done
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
if grep -Fq 'Surface `improve` only when this retro completes an epic-level group' \
    "$KIT/skills/sdlc/SKILL.md" \
  && grep -Fq 'Do not surface these options after a leaf-task retro' \
    "$KIT/skills/sdlc/SKILL.md" \
  && grep -Fq 'If there is no such enclosing group, skip the' \
    "$KIT/skills/sdlc/SKILL.md"; then
  pass "skills/sdlc/SKILL.md: improve is surfaced only after an epic-level group completes"
else
  fail "skills/sdlc/SKILL.md: improve must not be surfaced after every task retro"
fi
sdlc_text="$(tr '\n' ' ' < "$KIT/skills/sdlc/SKILL.md" | tr -s ' ')"
if grep -Fq 'Per-task learning, final epic reconciliation' \
    "$KIT/skills/sdlc/SKILL.md" \
  && printf '%s' "$sdlc_text" | grep -Fq 'run the Retro learning pass after every landed task' \
  && printf '%s' "$sdlc_text" | grep -Fq 'If child tasks remain, do not reconcile feature artifacts or update the parent epic checklist.' \
  && printf '%s' "$sdlc_text" | grep -Fq 'If the leaf-task Retro produces no repository edit, continue to the next task without a landing action.' \
  && grep -Fq 'PRD, ADRs, frozen contract, architecture, security, test strategy, and tracker' \
    "$KIT/skills/sdlc/SKILL.md" \
  && grep -Fq 'When all child tasks are complete' "$KIT/skills/sdlc/SKILL.md" \
  && printf '%s' "$sdlc_text" | grep -Fq 'Land all final reconciliation repository edits on the default branch before completing the parent epic.' \
  && printf '%s' "$sdlc_text" | grep -Fq 'Do not report the epic done or offer `improve` until its authoritative tracker record is complete.' \
  && printf '%s' "$sdlc_text" | grep -Fq 'Local-only: add one feature/epic row and its child task rows to `docs/progress.md`' \
  && grep -Fq '| Key | Feature / epic | PRD | Status |' "$KIT/templates/docs/progress.md" \
  && grep -Fq '| # | Parent | Task | Status | PR | Notes |' "$KIT/templates/docs/progress.md"; then
  pass "skills/sdlc/SKILL.md: leaf retros keep learnings but defer epic reconciliation"
else
  fail "skills/sdlc/SKILL.md: Stage 8 must preserve per-task learnings and reconcile after the final child"
fi
if grep -Fq 'ask to land the full context + foundation' "$KIT/skills/sdlc/SKILL.md" \
  && grep -Fq 'ask to land the reconstructed package' "$KIT/skills/sdlc/SKILL.md" \
  && grep -Fq 'ask to commit the full Stage 1–2 planning package to `main`' \
    "$KIT/skills/sdlc/SKILL.md" \
  && grep -Fq 'At the Stage 0 foundation gate, ask to land' "$KIT/AGENTS.md" \
  && grep -Fq 'Commit the feature planning package once, after Stage 2' "$KIT/AGENTS.md"; then
  pass "Stage 0 and Stage 1–2 planning packages have explicit landing requests"
else
  fail "planning packages must have explicit landing requests before Stage 4"
fi
feature_start_text="$(tr '\n' ' ' < "$KIT/skills/feature-start/SKILL.md" | tr -s ' ')"
stage_four_agents="$(grep -m1 '^| 4 ' "$KIT/AGENTS.md" || true)"
stage_four_sdlc="$(grep -m1 '^| 4 ' "$KIT/skills/sdlc/SKILL.md" || true)"
if printf '%s' "$feature_start_text" | grep -Fq 'The plan is a transient gate artifact, not repository documentation.' \
  && printf '%s' "$feature_start_text" | grep -Fq 'Do not create `docs/superpowers/plans/` or another plan file unless the human asks for a durable plan.' \
  && printf '%s' "$feature_start_text" | grep -Fq 'Keep it proportional to this one task and easy to scan' \
  && printf '%s' "$sdlc_text" | grep -Fq 'follow `feature-start` for its compact in-session format; no file path exists unless the human requested a durable plan' \
  && printf '%s' "$stage_four_agents" | grep -Fq 'in-session' \
  && printf '%s' "$stage_four_sdlc" | grep -Fq 'in-session'; then
  pass "Stage 4 uses a compact in-session plan without a repository file"
else
  fail "Stage 4 plans must stay compact and in-session unless the human requests a durable file"
fi
readme_text="$(tr '\n' ' ' < "$KIT/README.md" | tr -s ' ')"
if printf '%s' "$readme_text" | grep -Fq 'You can install other skills' \
  && printf '%s' "$readme_text" | grep -Fq 'do not become pipeline stages'; then
  pass "README.md: manifest scope and extra-skill behavior are accurate"
else
  fail "README.md: manifest statement must cover supported entries and extra-skill behavior"
fi
install_text="$(tr '\n' ' ' < "$KIT/INSTALL.md" | tr -s ' ')"
if printf '%s' "$install_text" | grep -Fq 'You may install other skills' \
  && printf '%s' "$install_text" | grep -Fq 'without becoming pipeline stages'; then
  pass "INSTALL.md: manifest scope and extra-skill behavior are accurate"
else
  fail "INSTALL.md: manifest statement must cover supported entries and extra-skill behavior"
fi
if grep -Fq '.agents/skills/sdlc/SKILL.md' "$KIT/INSTALL.md" \
  && grep -Fq '$SKILLS_DIR/sdlc/SKILL.md' "$KIT/INSTALL.md" \
  && grep -Fq 'project-root `required-skills.yml`' "$KIT/INSTALL.md"; then
  pass "INSTALL.md: pipeline promotion points to installed conductor and manifest"
else
  fail "INSTALL.md: pipeline promotion must name the installed conductor and manifest"
fi
template_guidance_ok=1
for doc_template in \
  templates/docs/prd/TEMPLATE.md \
  templates/docs/adr/TEMPLATE.md \
  templates/docs/architecture.md \
  templates/docs/security.md \
  templates/docs/contracts/README.md \
  templates/docs/test-strategy.md \
  templates/docs/runbook.md \
  templates/docs/context.md; do
  grep -Fq 'Follow the documentation writing standard in AGENTS.md.' "$KIT/$doc_template" \
    || template_guidance_ok=0
done
if grep -Fq '## Communication standard' "$KIT/AGENTS.md" \
  && grep -Fq '## Documentation writing standard' "$KIT/AGENTS.md" \
  && printf '%s' "$sdlc_text" | grep -Fq 'communication and documentation writing standards in `AGENTS.md`' \
  && printf '%s' "$sdlc_text" | grep -Fq 'single source for both' \
  && awk '
    /^## Scan$/ { scan = NR }
    /^## Problem$/ { problem = NR }
    scan && !problem && /^- \*\*Scope:\*\*/ { scope = 1 }
    scan && !problem && /^- \*\*Key decisions:\*\*/ { decisions = 1 }
    scan && !problem && /^- \*\*Constraints:\*\*/ { constraints = 1 }
    scan && !problem && /^- \*\*Links:\*\*/ { links = 1 }
    scan && !problem && /^- \*\*Open questions:\*\*/ { questions = 1 }
    END {
      exit !(scan && problem && scan < problem && scope && decisions &&
             constraints && links && questions)
    }
  ' "$KIT/templates/docs/prd/TEMPLATE.md" \
  && [ "$template_guidance_ok" -eq 1 ]; then
  pass "communication and documentation standards are single-sourced; PRD starts with scan fields"
else
  fail "communication/documentation guidance must be single-sourced and the PRD scan must precede detail"
fi
for f in README.md CHEATSHEET.md; do
  grep -Fq '`address-review`' "$KIT/$f" \
    && pass "$f: standalone address-review skill is discoverable" \
    || fail "$f: standalone address-review skill must be named"
done

echo "[11] Markdown emphasis style"
emphasis_hits=""
while IFS= read -r -d '' f; do
  hits="$(grep -nE '(^|[[:space:](>])\*([^*[:space:]]|[^*[:space:]][^*]*[^*[:space:]])\*($|[[:space:].,;:!?)])' "$f" || true)"
  [ -z "$hits" ] || emphasis_hits+="${f#"$KIT/"}:"$'\n'"$hits"$'\n'
done < <(
  find \
    "$KIT/AGENTS.md" \
    "$KIT/CHANGELOG.md" \
    "$KIT/CHEATSHEET.md" \
    "$KIT/CONTRIBUTING.md" \
    "$KIT/EXAMPLE.md" \
    "$KIT/INSTALL.md" \
    "$KIT/README.md" \
    "$KIT/skills" \
    "$KIT/templates" \
    -type f -name '*.md' -print0
)
if [ -z "$emphasis_hits" ] \
  && grep -Fq 'Use underscores (`_text_`) for emphasis.' "$KIT/AGENTS.md"; then
  pass "Markdown emphasis uses underscores"
else
  fail "single emphasis must use underscores and AGENTS.md must state the convention"
  printf '%s' "$emphasis_hits" | sed 's/^/      /'
fi

echo
[ "$FAIL" -eq 0 ] && echo "ALL CHECKS PASSED" || echo "SOME CHECKS FAILED"
exit "$FAIL"
