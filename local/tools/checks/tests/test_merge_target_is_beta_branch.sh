#!/bin/bash
# Three-direction test for check_merge_target_is_beta_branch.py:
#   1. a fixture where origin/precedent-beta-v01 IS an ancestor of
#      origin/main -- the PR #89 mistake -- require the check to fire (exit 1);
#   2. a fixture where the two branches have diverged, the normal
#      mid-restructure state -- require the check to stay clean (exit 0);
#   3. a fixture missing one of the two refs -- require exit 2 (SKIPPED),
#      never a silent pass, since an absent ref means the comparison the
#      check exists to make did not happen.
#
# Fixtures rather than the real repo: direction 1 asserts a condition that
# must NEVER be true here, so it cannot be planted in place -- and the whole
# point of this practice is that nobody arranges it accidentally.
set -euo pipefail
cd "$(dirname "$0")/../../../.."          # local/tools/checks/tests -> repo root
ROOT="$(pwd)"
CHECK="$ROOT/local/tools/checks/check_merge_target_is_beta_branch.py"
PRACTICE="$ROOT/local/practices/merge-target-is-beta-branch.md"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

# A fixture repo laid out exactly as the check expects: the script four
# levels down from the root it audits, and the practice file beside it.
make_fixture() {                                   # $1 = name
  local d="$SCRATCH/$1"
  mkdir -p "$d/local/tools/checks" "$d/local/practices"
  cp "$CHECK" "$d/local/tools/checks/"
  cp "$PRACTICE" "$d/local/practices/"
  git -C "$d" init -q -b main
  git -C "$d" config user.name Test
  git -C "$d" config user.email test@example.com
  git -C "$d" add -A
  git -C "$d" commit -q -m "fixture base"
  echo "$d"
}

run() {                                            # $1 = dir; echoes exit code
  local status=0
  ( cd "$1" && python3 local/tools/checks/check_merge_target_is_beta_branch.py \
      >/dev/null 2>&1 ) || status=$?
  echo "$status"
}

# --- 1. beta merged into main: must fire -------------------------------
D="$(make_fixture merged)"
git -C "$D" branch precedent-beta-v01
git -C "$D" update-ref refs/remotes/origin/main "$(git -C "$D" rev-parse main)"
git -C "$D" update-ref refs/remotes/origin/precedent-beta-v01 \
    "$(git -C "$D" rev-parse precedent-beta-v01)"
if [ "$(run "$D")" != "1" ]; then
  echo "FAIL: did not fire when origin/precedent-beta-v01 is an ancestor of origin/main" >&2
  exit 1
fi
echo "ok: fires on planted violation"

# --- 2. diverged, the normal state: must stay clean --------------------
D="$(make_fixture diverged)"
git -C "$D" checkout -q -b precedent-beta-v01
git -C "$D" commit -q --allow-empty -m "beta-only work"
git -C "$D" update-ref refs/remotes/origin/main "$(git -C "$D" rev-parse main)"
git -C "$D" update-ref refs/remotes/origin/precedent-beta-v01 \
    "$(git -C "$D" rev-parse precedent-beta-v01)"
if [ "$(run "$D")" != "0" ]; then
  echo "FAIL: fired on a diverged beta branch, which is the expected state" >&2
  exit 1
fi
echo "ok: clean when the branches have diverged"

# --- 3. a missing ref: must SKIP, never pass ---------------------------
D="$(make_fixture unfetched)"
git -C "$D" update-ref refs/remotes/origin/main "$(git -C "$D" rev-parse main)"
if [ "$(run "$D")" != "2" ]; then
  echo "FAIL: did not exit 2 (SKIPPED) when origin/precedent-beta-v01 is absent -- a comparison that could not run must never read as a pass" >&2
  exit 1
fi
echo "ok: skips (exit 2) when a ref is missing"

# --- 4. the real repo: must be clean or honestly skip ------------------
status=0
python3 "$CHECK" >/dev/null 2>&1 || status=$?
if [ "$status" -eq 2 ]; then
  echo "SKIPPED: origin/main and origin/precedent-beta-v01 are not both fetched here -- not a check failure"
elif [ "$status" -ne 0 ]; then
  echo "FAIL: not clean on the real repo" >&2
  exit 1
else
  echo "ok: clean on real content"
fi
