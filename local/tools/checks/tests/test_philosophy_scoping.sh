#!/bin/bash
# Firing tests for the two philosophy/ checks, in both directions each:
# a planted violation must exit 1, the real repo must exit 0, and a repo
# with no philosophy/ at all must exit 2 (SKIPPED), never a silent pass.
#
# Fixtures rather than the real tree, for check_philosophy_is_not_repo_policy
# especially: direction 1 plants exactly the condition that must never be
# true here, and planting it in place would mean committing a violation to
# find out whether the check notices.
set -euo pipefail
cd "$(dirname "$0")/../../../.."          # local/tools/checks/tests -> repo root
ROOT="$(pwd)"
POLICY="$ROOT/local/tools/checks/check_philosophy_is_not_repo_policy.py"
SOURCE="$ROOT/local/tools/checks/check_philosophy_declares_its_source.py"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

# A fixture laid out exactly as the checks expect: the script four levels
# down from the root it audits, its practice file beside it, and a
# philosophy/ tree to audit.
make_fixture() {                                   # $1 = name
  local d="$SCRATCH/$1"
  mkdir -p "$d/local/tools/checks" "$d/local/practices" \
           "$d/practices" "$d/philosophy"
  cp "$POLICY" "$SOURCE" "$d/local/tools/checks/"
  cp "$ROOT/local/practices/philosophy-is-not-repo-policy.md" \
     "$ROOT/local/practices/philosophy-declares-its-source.md" \
     "$d/local/practices/"
  printf '<!-- Last updated: 2026-01-01; written here. -->\n\n# Fixture\n' \
    > "$d/philosophy/FIXTURE.md"
  echo "$d"
}

# Write a minimal practice file. $1 = dir, $2 = repo-relative path,
# $3 = applies_to value, $4 = the ## Rule body.
write_practice() {
  cat > "$1/$2" <<EOF
---
slug:        fixture-practice
title:       A fixture
tier:        on-demand
severity:    default
applies_to:  $3
occasion:    "a fixture"
checked_by:  null
status:      active
---
## Rule
$4

## Story
A fixture.
EOF
}

run() {                                            # $1 = dir, $2 = script
  local status=0
  ( cd "$1" && python3 "local/tools/checks/$2" >/dev/null 2>&1 ) || status=$?
  echo "$status"
}

# === check_philosophy_is_not_repo_policy ==============================

# --- 1. a Rule citing an essay: must fire ------------------------------
D="$(make_fixture rule-cites-essay)"
write_practice "$D" "practices/fixture-practice.md" '["**"]' \
  'Follow the argument in philosophy/OUR_PHILOSOPHY.md whenever you write.'
if [ "$(run "$D" check_philosophy_is_not_repo_policy.py)" != "1" ]; then
  echo "FAIL: did not fire on a ## Rule citing a philosophy/ path" >&2
  exit 1
fi
echo "ok: fires when a Rule cites an essay as its authority"

# --- 2. the same citation in ## Why: must stay clean -------------------
# The distinction the practice turns on -- an essay may EXPLAIN a rule.
D="$(make_fixture essay-in-why)"
cat > "$D/practices/fixture-practice.md" <<'EOF'
---
slug:        fixture-practice
title:       A fixture
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a fixture"
checked_by:  null
status:      active
---
## Rule
Bold the key phrases in a document.

## Why
The reasoning is set out at length in philosophy/OUR_PHILOSOPHY.md.

## Story
A fixture.
EOF
if [ "$(run "$D" check_philosophy_is_not_repo_policy.py)" != "0" ]; then
  echo "FAIL: fired on a philosophy/ citation in ## Why, which is allowed" >&2
  exit 1
fi
echo "ok: clean when an essay only explains a rule"

# --- 3. a philosophy-scoped practice in the EXPORTED catalogue ---------
D="$(make_fixture exported-philosophy-scope)"
write_practice "$D" "practices/fixture-practice.md" '["philosophy/**"]' \
  'Do a thing.'
if [ "$(run "$D" check_philosophy_is_not_repo_policy.py)" != "1" ]; then
  echo "FAIL: did not fire on a philosophy-scoped practice in practices/" >&2
  exit 1
fi
echo "ok: fires on a philosophy-scoped rule in the exported catalogue"

# --- 4. the same scope in local/practices/: must stay clean ------------
# This is where the two practices this test covers actually live.
D="$(make_fixture local-philosophy-scope)"
write_practice "$D" "local/practices/fixture-practice.md" '["philosophy/**"]' \
  'Do a thing.'
if [ "$(run "$D" check_philosophy_is_not_repo_policy.py)" != "0" ]; then
  echo "FAIL: fired on a philosophy-scoped practice in local/practices/, which is exactly where one belongs" >&2
  exit 1
fi
echo "ok: clean when a philosophy-scoped rule is repo-local"

# === check_philosophy_declares_its_source =============================

# --- 5. a document with no provenance line: must fire ------------------
D="$(make_fixture no-provenance)"
printf '# An Essay\n\nWith no provenance line.\n' > "$D/philosophy/ORPHAN.md"
if [ "$(run "$D" check_philosophy_declares_its_source.py)" != "1" ]; then
  echo "FAIL: did not fire on a philosophy/ document with no provenance line" >&2
  exit 1
fi
echo "ok: fires on a document that does not say where it came from"

# --- 6. a comment naming no origin: must fire --------------------------
D="$(make_fixture empty-comment)"
printf '<!-- Last updated: 2026-01-01 -->\n\n# An Essay\n' \
  > "$D/philosophy/VAGUE.md"
if [ "$(run "$D" check_philosophy_declares_its_source.py)" != "1" ]; then
  echo "FAIL: did not fire on a comment that names no source" >&2
  exit 1
fi
echo "ok: fires on a provenance line that names no origin"

# --- 7. no philosophy/ at all: must SKIP, never pass -------------------
for script in check_philosophy_is_not_repo_policy.py \
              check_philosophy_declares_its_source.py; do
  D="$(make_fixture "no-philosophy-$script")"
  rm -rf "$D/philosophy"
  if [ "$(run "$D" "$script")" != "2" ]; then
    echo "FAIL: $script did not exit 2 (SKIPPED) with no philosophy/ tree -- a check that could not run must never read as a pass" >&2
    exit 1
  fi
done
echo "ok: both skip (exit 2) when there is no philosophy/ to audit"

# --- 8. the real repo: both must be clean ------------------------------
for script in "$POLICY" "$SOURCE"; do
  status=0
  python3 "$script" >/dev/null 2>&1 || status=$?
  if [ "$status" -ne 0 ]; then
    echo "FAIL: $(basename "$script") is not clean on the real repo (exit $status)" >&2
    python3 "$script" >&2 || true
    exit 1
  fi
done
echo "ok: both clean on real content"
