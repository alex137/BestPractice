#!/bin/bash
# Claude Code adapter: PreToolUse hook that REFUSES a `git push` whose
# history does not pass tools/checks/check_commit_author.py and
# tools/checks/check_buenos_aires_dates.py.
#
# WHY THIS EXISTS (2026-09-21, practice: cite-the-incident). These two
# checks had just lost their last enforced home, and it took two moves to
# happen rather than one, which is why neither move looked like a mistake
# on the day it was made:
#
#   1. commit-identity.yml ran them on every non-draft pull request. On
#      2026-09-19 they were folded into precedent-check.yml as named steps
#      and that workflow was PAUSED -- the pause was safe precisely because
#      the fold had a destination.
#   2. On 2026-09-21 source-sets-run-no-ci deleted precedent-check.yml.
#      The destination went with it, and nothing re-read the paused
#      workflow's header to notice that its reason for being paused had
#      just stopped being true.
#
# So both checks ran nowhere after a push. Morgan, on being shown it:
# rehome them "onto that repo's own push gate rather than any workflow: a
# local gate costs no Actions minutes, so it survives the no-CI rule
# unchanged, which the CI fold did not."
#
# WHY A CLAUDE CODE HOOK AND NOT .git/hooks/pre-push. This machine sets
# `core.hooksPath` GLOBALLY to /root/.config/precedent/git-hooks, so a
# repo-local .git/hooks/pre-push is never executed -- checked, 2026-09-21,
# and this repo's own .git/hooks/pre-commit is a dead copy for that exact
# reason. Writing into the global directory instead would put this repo's
# checks on every push from every repository on the container, and would
# live outside the tree where nothing tracks it. This file is tracked,
# wired by tracked settings.json, and scoped to this repo alone.
#
# WHY PUSH AND NOT COMMIT, unlike doc-lint-gate.sh beside it. Both checks
# are scope `tree` -- they walk `git log` over every commit reachable from
# HEAD -- so a pre-commit gate cannot see the commit it is gating; that is
# the "a commit cannot be audited before it exists" blind spot
# commit-identity.yml was written to close. Push is the first moment the
# commit exists and the last one before it is published.
#
# WHY NOT LEAVE IT TO precedent_check.py. That runs both, but tree-scope
# checks there run on a ROTATION SLICE -- "covered within 10 commits", in
# its own output -- so a given push is not necessarily audited. These run
# every time.
#
# FAIL-CLOSED ON A FINDING, FAIL-OPEN ON THE PLUMBING, exactly as
# doc-lint-gate.sh does and for the same reason (practice: fail-gracefully):
# no jq, no python3, no git, no check script, an unparseable payload, or a
# check that CRASHES rather than reporting -- all exit 0, loudly on stderr
# where there is something to say. A gate that breaks a session over its
# own missing dependency is a gate somebody disables.
set -euo pipefail

input="$(cat)"

command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

cmd="$(printf '%s' "$input" \
  | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
[[ -n "$cmd" ]] || exit 0

# THE COMMAND WITH ITS QUOTED TEXT BLANKED (2026-09-30), so the tests below
# read only what the shell will run. A `|` or `;` inside a quoted argument
# is not a pipe: `grep "a\|git push"` read as a push once, ran the full push
# check for 766 s and refused a read-only grep
# (todo-2026-09-29-push-gate-reads-a-quoted-pipe-as-a-command). Quoted
# strings and heredoc bodies become spaces, newlines kept; everything else
# is unchanged. The same block sits in every hook that asks "does this
# command run X"; verify_harness keeps the copies identical. No python3
# result: the raw command, as before.
bare="$(printf '%s' "$cmd" | python3 -c '
import re, sys
s = sys.stdin.read(); out = []; i = 0; n = len(s)
Q, D, B = chr(39), chr(34), chr(92)
blank = lambda t: re.sub(r"[^\n]", " ", t)
while i < n:
    c = s[i]
    if c == B and i + 1 < n:
        out.append(s[i:i + 2]); i += 2; continue
    if c in (Q, D):
        j = i + 1
        while j < n and s[j] != c:
            j += 2 if (c == D and s[j] == B) else 1
        out.append(c + blank(s[i + 1:min(j, n)]) + (c if j < n else "")); i = j + 1; continue
    m = re.match(r"<<-?[ \t]*([" + Q + D + r"]?)([A-Za-z_]\w*)\1", s[i:])
    if m:
        out.append(m.group(0)); i += m.end()
        nl = s.find("\n", i)
        if nl < 0:
            continue
        out.append(s[i:nl + 1]); i = nl + 1
        end = re.search(r"(?m)^[ \t]*" + re.escape(m.group(2)) + r"[ \t]*$", s[i:])
        stop = i + end.start() if end else n
        out.append(blank(s[i:stop])); i = stop; continue
    out.append(c); i += 1
sys.stdout.write("".join(out))
' 2>/dev/null)" || bare="$cmd"
[[ -n "$bare" ]] || bare="$cmd"

# Only a real `git push`, in command position. `git push` inside a heredoc,
# a commit message or an echo is not one -- the same discipline
# doc-lint-gate.sh applies to `git commit`, learned from a check that cried
# wolf on a quoted mention (gotcha-2026-09-21).
printf '%s' "$bare" \
  | grep -qE '(^|[|;&]|&&|\|\||\$\()[[:space:]]*git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?push\b' \
  || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-.}"

# A `git -C <path> push` aimed at a DIFFERENT repository is not this gate's
# business: these checks live in this repo's tools/ and judge this repo's
# history. A bare `git push` is assumed to mean this one -- the hook cannot
# see the Bash tool's working directory, so a `cd elsewhere && git push`
# would be judged here; that direction fails safe (it can only report on a
# tree this repo owns) and is the same limitation doc-lint-gate.sh carries.
# `|| true` is load-bearing under `set -o pipefail`: grep exits 1 when the
# command carries no `-C`, which is the ORDINARY case (`git push origin X`),
# and without it the whole hook aborted before running a single check --
# silently, with an exit status nothing reads. Caught testing the clean
# direction, which is the one direction a broken gate looks fine in.
target="$(printf '%s' "$cmd" \
  | grep -oE '\-C[[:space:]]+[^[:space:]]+' \
  | head -n1 | sed -E 's/^-C[[:space:]]+//' || true)"
if [[ -n "$target" ]]; then
    target_top="$(git -C "$target" rev-parse --show-toplevel 2>/dev/null || true)"
    here_top="$(git -C "$project_dir" rev-parse --show-toplevel 2>/dev/null || true)"
    [[ -n "$target_top" && "$target_top" == "$here_top" ]] || exit 0
fi

findings=""
crashed=""

# BOTH ARE RUN, ALWAYS, never short-circuiting on the first failure. They
# share one grandfather list and a single cause trips both at once --
# identity.json's second grandfathered entry is exactly that -- so showing
# only the first finding hides half the picture and invites fixing one
# value and re-running. This is commit-identity.yml's own `!cancelled()`
# reasoning, carried over intact.
for check in check_commit_author check_buenos_aires_dates; do
    script="$project_dir/tools/checks/$check.py"
    [[ -f "$script" ]] || continue
    set +e
    out="$(cd "$project_dir" && python3 "$script" 2>&1)"
    rc=$?
    set -e

    # A traceback is a broken checker, not a finding about the history --
    # the distinction doc-lint-gate.sh had to learn after handing back a
    # Python ImportError as though it were a lint result. Classified FIRST,
    # so a crash can never be read as a violation whatever it exited with.
    if printf '%s' "$out" | grep -q '^Traceback (most recent call last):'; then
        crashed+="
=== $check CRASHED ===
$out
"
        continue
    fi

    case "$rc" in
        0) ;;
        # SKIPPED. Exit 2 means no declared identity resolved, which is the
        # expected and correct state in a SHARED repo -- and is itself a
        # defect HERE: identity.json is tracked at this repo's root and is
        # rung 2 of the resolution ladder, so a skip means the check could
        # not read its own set and this gate enforced nothing. Refusing on
        # it is commit-identity.yml's "Refuse a silent identity skip" step,
        # which existed because a silent skip reads exactly like a pass.
        # Outside an individual source (no identity.json at the root) a skip
        # is the right answer, not a failure: the timezone check binds only
        # the person's own repo (Morgan, 2026-09-25), and the author check
        # has no declared person to hold a shared repo to.
        2) [[ -f "$project_dir/identity.json" ]] || continue
           findings+="
=== $check: SKIPPED (exit 2), which in THIS repo is a failure ===
No declared identity resolved, so the check enforced nothing. identity.json
is tracked at this repo's root and is rung 2 of the ladder, so this means
the check could not read it.
$out
" ;;
        1) findings+="
=== $check ===
$out
" ;;
        *) crashed+="
=== $check exited $rc, which is not a result this check defines ===
$out
" ;;
    esac
done

if [[ -n "$crashed" ]]; then
    echo "WARN: commit-identity-push-gate: a check CRASHED rather than reporting findings, so this push was NOT fully audited. The gate is failing open. Fix the check -- until you do, nothing is auditing commit authorship or timezone before it is published:" >&2
    printf '%s\n' "$crashed" >&2
fi

[[ -n "$findings" ]] || exit 0

reason="The commit-identity push gate REFUSED this push.

These two checks are scope \`tree\`: they audit every commit reachable from
HEAD, not just the ones this push adds. They ran in GitHub Actions until
2026-09-21, when a practice source stopped running CI at all; this hook is
what replaced them, which makes it the only thing standing between a
mis-authored commit and a published branch.
$findings
Fix it before the commit is published. On an UNPUSHED commit this is one
\`git commit --amend --reset-author\` (re-run under
TZ=America/Argentina/Buenos_Aires for the offset); once it is on a shared
branch, no-rewrite-for-warnings applies and the only honest route left is a
grandfathered_commit_shas entry in identity.json with a reason. That
asymmetry is the whole reason this gate sits before the push rather than
after it.

Nothing lets a push past this: fix the commit as above, then push again."

printf '%s' "$reason" | jq -Rs '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: .
  }
}'
exit 0
