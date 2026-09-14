#!/bin/bash
# Four-direction test for check_install_declares_its_scope.py:
#   1. install docs declaring the scope, its counterpart, and the optional
#      files as deferred -- require clean (exit 0) and silent;
#   2. a doc with no scope declaration -- require exit 1 naming THAT;
#   3. a doc declaring the scope but never its counterpart -- require exit 1
#      naming THAT, separately from 2;
#   4. a doc naming VOICE.md and STYLEGUIDE.md together with no deferral
#      marker -- require exit 1 naming THAT;
#   5. a repo with neither document -- require exit 2 (SKIPPED), never a
#      silent pass: a consuming repo's install path lives upstream.
#
# Direction 6 is the regression that motivated the whole check: prose that
# says "do NOT walk them through" must NOT fire. A check that cannot tell an
# instruction from its negation is worse than no check, and the first draft
# of this one got it wrong -- it flagged three correct passages in the real
# INSTALL.md.
#
# practice: control-asserts-which-failure -- every failing direction asserts
# the printed message, not merely a non-zero exit. A check that exits 1 for
# an unrelated reason (a missing practice file, a traceback) would satisfy
# the exit code alone and prove nothing.
set -euo pipefail
cd "$(dirname "$0")/../../../.."          # local/tools/checks/tests -> repo root
ROOT="$(pwd)"
CHECK="$ROOT/local/tools/checks/check_install_declares_its_scope.py"
PRACTICE="$ROOT/local/practices/install-declares-its-scope.md"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

fail=0
ok()  { echo "  ok   -- $1"; }
bad() { echo "  FAIL -- $1"; fail=1; }

# A fixture laid out exactly as the check expects: the script four levels
# down from the root it audits, the practice file beside it.
make_fixture() {                                   # $1 = name
  local d="$SCRATCH/$1"
  mkdir -p "$d/local/tools/checks" "$d/local/practices"
  cp "$CHECK" "$d/local/tools/checks/"
  cp "$PRACTICE" "$d/local/practices/"
  echo "$d"
}

run() {                                            # $1 = fixture dir
  set +e
  OUT="$(python3 "$1/local/tools/checks/check_install_declares_its_scope.py" 2>&1)"
  RC=$?
  set -e
}

GOOD_SCOPE='## Essentials Only
An install does the essentials and stops. A refinement is named once and
deferred.

What is never deferred: the blocklist, the commit identity, the audit.
'
GOOD_FILES='`VOICE.md` and `STYLEGUIDE.md` ship as skeletons and stay that way.
'

# --- 1. clean -------------------------------------------------------------
d=$(make_fixture clean)
printf '%s\n%s' "$GOOD_SCOPE" "$GOOD_FILES" > "$d/INSTALL.md"
printf '%s\n%s' "$GOOD_SCOPE" "$GOOD_FILES" > "$d/SETUP.md"
run "$d"
if [ "$RC" -eq 0 ] && [ -z "$OUT" ]; then ok "clean docs pass silently"
else bad "clean docs should exit 0 and print nothing; rc=$RC out=$OUT"; fi

# --- 2. no scope declaration ---------------------------------------------
d=$(make_fixture noscope)
printf 'Install it.\n\nWhat is never deferred: the audit.\n%s' "$GOOD_FILES" > "$d/INSTALL.md"
run "$d"
if [ "$RC" -eq 1 ] && grep -q 'nothing declares the essentials-only scope' <<<"$OUT"; then
  ok "missing scope declaration is named"
else bad "expected the scope finding; rc=$RC out=$OUT"; fi

# --- 3. scope but no counterpart -----------------------------------------
d=$(make_fixture nocounterpart)
printf '## Essentials Only\nAn install does the essentials and stops.\n\n%s' "$GOOD_FILES" > "$d/INSTALL.md"
run "$d"
if [ "$RC" -eq 1 ] && grep -q 'counterpart is not' <<<"$OUT"; then
  ok "missing counterpart is named, separately from the scope"
else bad "expected the counterpart finding; rc=$RC out=$OUT"; fi

# --- 4. the optional files named as an instruction ------------------------
d=$(make_fixture instruction)
printf '%s\nWalk them through `VOICE.md` and fill in `STYLEGUIDE.md` from their brand guideline.\n' "$GOOD_SCOPE" > "$d/INSTALL.md"
run "$d"
if [ "$RC" -eq 1 ] && grep -q 'no deferral marker' <<<"$OUT"; then
  ok "an instruction to fill the optional files in is caught"
else bad "expected the deferral-marker finding; rc=$RC out=$OUT"; fi

# --- 5. neither document --------------------------------------------------
d=$(make_fixture absent)
run "$d"
if [ "$RC" -eq 2 ] && grep -q 'SKIPPED' <<<"$OUT"; then
  ok "a repo with no install path SKIPS, and is not a silent pass"
else bad "expected exit 2 and SKIPPED; rc=$RC out=$OUT"; fi

# --- 6. the negation must NOT fire ---------------------------------------
# The failure mode this check exists to avoid in itself.
d=$(make_fixture negation)
printf '%s\nBoth `VOICE.md` and `STYLEGUIDE.md` ship empty. Do not walk them\nthrough the sections, and do not ask whether a brand guideline exists.\n' "$GOOD_SCOPE" > "$d/INSTALL.md"
run "$d"
if [ "$RC" -eq 0 ]; then ok "prose forbidding the walkthrough does not fire"
else bad "the negation fired -- the check cannot tell an instruction from its negation; out=$OUT"; fi

echo
if [ "$fail" -eq 0 ]; then echo "test_install_declares_its_scope: all directions ok"; else
  echo "test_install_declares_its_scope: FAILURES"; fi
exit "$fail"
