#!/bin/bash
# Claude Code adapter: PreToolUse hook that REFUSES a `git commit` whose
# staged Markdown does not pass tools/doc_lint.py.
#
# WHY THIS EXISTS (2026-09-21, practice: cite-the-incident). The Markdown
# lint left GitHub Actions entirely that day: under this system's founding
# assumption -- every edit arrives through a cloud session, never a local
# checkout and never the GitHub web UI -- CI was re-running a check the
# session had already run, at a measured 350 billed minutes over 19 days in
# one repository (spec/BILLING_FLOOR.md).
#
# The premise that made that safe was "the light check gates a commit". It
# did not. AGENTS.md SAID so, and sessions did it, but nothing refused a
# commit that skipped it -- so removing CI would have turned a real backstop
# into a habit. Morgan, on being told: "I want to be 100% sure that we are
# still doing markdown checks BEFORE handing it over to github."
#
# A convention cannot be 100%. This can. It costs no Actions minutes,
# and it catches the failure EARLIER than CI did -- before the commit
# rather than after the push.
#
# FAIL-CLOSED ON THE LINT, FAIL-OPEN ON THE PLUMBING. A doc_lint failure
# blocks the commit, because that is the whole point. Everything else --
# no jq, no python3, no doc_lint.py, an unparseable payload, a commit that
# stages no Markdown -- exits 0 silently. A gate that breaks a session over
# its own missing dependency is a gate somebody disables (practice:
# fail-gracefully).
set -euo pipefail

input="$(cat)"

command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
command -v git >/dev/null 2>&1 || exit 0

cmd="$(printf '%s' "$input" \
  | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
[[ -n "$cmd" ]] || exit 0

# Only a real `git commit`. `git commit` appearing inside a heredoc, a
# commit message, or an echo is not one -- so this requires it in command
# position, the same discipline precedent_check.py's
# shipped-template-carries-its-script had to learn after crying wolf on a
# quoted mention (gotcha-2026-09-21).
printf '%s' "$cmd" \
  | grep -qE '(^|[|;&]|&&|\|\||\$\()[[:space:]]*git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?commit\b' \
  || exit 0

project_dir="${CLAUDE_PROJECT_DIR:-.}"
script="$project_dir/tools/doc_lint.py"
[[ -f "$script" ]] || exit 0

# What this commit would actually publish: staged Markdown, nothing else.
# --cached, not the working tree: a file edited but not staged is not part
# of this commit and its state is none of this gate's business.
mapfile -t staged < <(git -C "$project_dir" diff --cached --name-only --diff-filter=ACM 2>/dev/null \
  | grep -E '\.md$' || true)
[[ ${#staged[@]} -gt 0 ]] || exit 0

# Paths that no longer exist (staged then deleted from disk) would make the
# linter error on a missing file rather than report a finding.
present=()
for f in "${staged[@]}"; do
  [[ -f "$project_dir/$f" ]] && present+=("$f")
done
[[ ${#present[@]} -gt 0 ]] || exit 0

# NO --strict, and the attempt is worth recording because it failed in an
# instructive direction. A strict mode promoting doc_lint's WARNING classes
# (unlinked file references, unglossed acronyms, target= anchors) to gating
# was built and then withdrawn the same hour: measured against INSTALL.md,
# a one-line edit that added nothing was refused over 111 unlinked
# references that had been there for weeks. Scoping the promotion to "lines
# this change touched" did not fix it either -- the warning classes are not
# line-attributed the way the gating classes are.
#
# A gate whose first act is to refuse work nobody just broke is a gate
# somebody switches off. So this runs doc_lint as it is: the gating classes
# only, already filtered to the lines this change touched. Morgan, on being
# shown the measurement: "Ok so let's not use --strict."
out="$(cd "$project_dir" && python3 "$script" "${present[@]}" 2>&1)" && exit 0

# A CRASH IS NOT A FINDING, and telling them apart is the difference
# between a gate and an outage. Caught while testing this hook's own clean
# direction: a fixture missing frontmatter_yaml made doc_lint.py die with
# an ImportError, the hook read "non-zero" as "the Markdown is bad", and
# it denied a commit whose Markdown was perfect -- handing back a Python
# traceback as though it were a lint finding.
#
# On a real repo with a half-vendored engine that blocks EVERY commit,
# with no way to tell from the message that the linter never ran. Fail
# open and say so on stderr: a broken linter is a problem to fix, not a
# reason nobody can commit.
if printf '%s' "$out" | grep -q '^Traceback (most recent call last):'; then
  echo "WARN: doc-lint-gate: tools/doc_lint.py CRASHED rather than reporting findings, so this commit was NOT checked. The gate is failing open. Fix the linter -- until you do, nothing is checking Markdown before it reaches the shared branch:" >&2
  printf '%s\n' "$out" >&2
  exit 0
fi

# doc_lint exited non-zero with real findings: refuse the commit and hand
# back its own output, which already names file, line and rule.
reason="doc_lint.py FAILED on the Markdown staged for this commit, so the
commit was refused. The Markdown lint no longer runs in GitHub Actions
(2026-09-21) -- this hook is what replaced it, which makes it the only
thing standing between a formatting error and the shared branch.

$out

Fix what it names, re-stage, and commit again. To commit anyway you must
say so explicitly and say why; do not work around this by unstaging the
Markdown."

printf '%s' "$reason" | jq -Rs '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: .
  }
}'
exit 0
