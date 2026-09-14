#!/bin/bash
# Three-direction test for check_park_it.py:
#   1. an instructions file that never names the phrase -- require the check
#      to fire (exit 1), and to say WHICH half is missing;
#   2. an instructions file carrying both the phrase and the disposition it
#      writes -- require it to stay clean (exit 0) and print nothing;
#   3. a repository with no instructions file at all -- require exit 2
#      (SKIPPED), never a silent pass: there is nowhere for the phrase to
#      live, so the question the check asks was not answered.
#
# Fixtures rather than the real repo: direction 1 asserts a state this repo
# must never be in again, which is the whole point of wiring the check.
#
# practice: control-asserts-which-failure -- every failing direction asserts
# the message, not merely a non-zero exit. A check that exits 1 for an
# unrelated reason (a missing practice file, a traceback) would satisfy the
# exit code alone and prove nothing.
set -euo pipefail
cd "$(dirname "$0")/../../../.."          # local/tools/checks/tests -> repo root
ROOT="$(pwd)"
CHECK="$ROOT/local/tools/checks/check_park_it.py"
PRACTICE="$ROOT/local/practices/park-it.md"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

fail=0
ok()   { echo "  ok   -- $1"; }
bad()  { echo "  FAIL -- $1"; fail=1; }

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
  OUT="$(python3 "$1/local/tools/checks/check_park_it.py" 2>&1)"
  RC=$?
  set -e
}

echo "test_park_it.sh"

# 1. the phrase is undocumented
d="$(make_fixture undocumented)"
printf '# Repo notes\n\nWork on a feature branch.\n' > "$d/AGENTS.md"
run "$d"
[ "$RC" = 1 ] && ok "an instructions file without the phrase fails (exit 1)" \
              || bad "expected exit 1, got $RC"
case "$OUT" in
  *"does not carry 'Park it'"*) ok "names the missing phrase" ;;
  *) bad "did not name the missing phrase; said: $OUT" ;;
esac
case "$OUT" in
  *"does not carry 'parked'"*) ok "names the missing disposition" ;;
  *) bad "did not name the missing disposition; said: $OUT" ;;
esac

# 1b. half-documented is still a violation -- the phrase with no meaning
# attached is exactly the state that sent a session off to ask.
d="$(make_fixture half)"
printf '# Repo notes\n\nWhen he says "Park it", do the right thing.\n' > "$d/AGENTS.md"
run "$d"
[ "$RC" = 1 ] && ok "the phrase without its meaning still fails" \
              || bad "expected exit 1 for a half-documented phrase, got $RC"
case "$OUT" in
  *"does not carry 'parked'"*) ok "and says which half is missing" ;;
  *) bad "did not name the missing half; said: $OUT" ;;
esac

# 2. properly documented
d="$(make_fixture documented)"
printf '# Repo notes\n\n"Park it" means mark the item `parked` and drop it.\n' > "$d/AGENTS.md"
run "$d"
[ "$RC" = 0 ] && ok "a documented phrase passes (exit 0)" \
              || bad "expected exit 0, got $RC; said: $OUT"
[ -z "$OUT" ] && ok "and prints nothing" || bad "expected silence, got: $OUT"

# 2b. CLAUDE.md alone counts -- a consuming repo may run the other way round
d="$(make_fixture claude-md)"
printf '"Park it" -- mark it `parked`.\n' > "$d/CLAUDE.md"
run "$d"
[ "$RC" = 0 ] && ok "CLAUDE.md alone satisfies it" || bad "expected exit 0, got $RC; said: $OUT"

# 3. nowhere to look
d="$(make_fixture no-instructions)"
run "$d"
[ "$RC" = 2 ] && ok "no instructions file reports NOT APPLICABLE (exit 2)" \
              || bad "expected exit 2, got $RC; said: $OUT"
case "$OUT" in
  *"NOT APPLICABLE"*) ok "and says so rather than passing" ;;
  *) bad "did not report NOT APPLICABLE; said: $OUT" ;;
esac

[ "$fail" = 0 ] && echo "test_park_it.sh: all directions ok" \
                || { echo "test_park_it.sh: FAILED"; exit 1; }
