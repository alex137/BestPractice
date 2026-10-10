#!/usr/bin/env bash
# Closes BestPractice's open main-test-failed issues once GitHub's test has
# passed on main's CURRENT head. Run only by .github/workflows/deep-check.yml,
# from two places: the deep-check job when its run on main passed, and the
# already-tested job when a push to main skipped the run because those exact
# files had already passed. Never on a pull request: a pull request into main
# passing says nothing about main.
#
# WHY (2026-10-10): issue #1036 stayed open about eleven hours while main's
# test passed at least three times, and the next session was sent to fix a
# main that was already green. The issue is only worth reading if it means
# "main is red right now".
#
# It closes nothing unless this run tested main's head: an older run
# finishing green after a newer one failed must not close a live failure.
# Every failure here is a warning and exit 0, so it can never turn a green
# run red.
#
# Needs: GH_TOKEN, GH_REPO, GITHUB_SHA, RUN_URL; HOW says how main passed.
set -u
label=main-test-failed
warn() { echo "::warning::$*"; exit 0; }

head=$(gh api "repos/$GH_REPO/commits/main" --jq .sha 2>/dev/null) \
  || warn "Could not read main's head; any open $label issue stays open."
[ -n "$head" ] || warn "Could not read main's head; any open $label issue stays open."
if [ "$head" != "$GITHUB_SHA" ]; then
  echo "main is at ${head:0:12} now, not ${GITHUB_SHA:0:12}; the run on main's head decides."
  exit 0
fi
open=$(gh issue list --label "$label" --state open --json number --jq '.[].number' 2>/dev/null) \
  || warn "Could not list the open $label issues."
[ -n "$open" ] || { echo "No open $label issue."; exit 0; }
body="GitHub's test passed on main @ ${GITHUB_SHA:0:12}, main's current head (${HOW:-passed}).

Run: $RUN_URL

Closed automatically: main is green again."
for n in $open; do
  if gh issue comment "$n" --body "$body" >/dev/null && gh issue close "$n" --reason completed >/dev/null; then
    echo "Closed #$n: main's test passed on its head."
  else
    echo "::warning::Could not close #$n; close it by hand if main is still green."
  fi
done
exit 0
