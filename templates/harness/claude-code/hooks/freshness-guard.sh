#!/bin/bash
#
# Claude Code adapter: never work on, or write to, a stale checkout.
#
# practice: session-bootstrap
#
# Install wherever this harness's settings.json wires its hooks FROM, and
# wire it twice there -- once as SessionStart, once as PreToolUse. That is
# usually .claude/hooks/freshness-guard.sh, which is what this line used to
# assert outright; a practice SET may instead wire its own tracked
# bootstrap/ directory, on purpose, so that one copy exists and nothing can
# drift from it. The header then named a path the file was not installed at,
# which is a header lying about its own location (practice: fix-the-original,
# reported 2026-09-14 from precedent-individual).
# The rule it implements -- verify and fast-forward the checkout before a
# session's first write, never after -- is not yet a universal practice
# here: promoting one is a separate, reviewed step. This is the mechanism,
# installed ahead of that.
#
# Two modes, wired as two different hooks in a project's own
# .claude/settings.json (see this adapter's own settings.json for the
# canonical wiring):
#
#   freshness-guard.sh session-start [BASE]
#       A SessionStart hook. Fetches, fast-forwards the current branch when
#       that is provably lossless, and reconciles it to origin when it has
#       diverged and the tree is clean -- safe here specifically because
#       SessionStart runs before this session's first turn, so nothing
#       reachable from local HEAD can be this session's own work yet. The
#       old tip is kept under refs/freshness-guard/pre-reset/, never just
#       discarded. Warns about anything it cannot fix that way (a dirty
#       tree, or the rescue-ref-then-reset sequence itself failing).
#       ALWAYS exits 0: a hook that can wedge a session over a freshness
#       question is a worse failure than the staleness it is guarding
#       against (fail-gracefully, same contract as
#       the adapter's session-start.sh).
#
#   freshness-guard.sh user-prompt [BASE]
#       A UserPromptSubmit hook, for the case neither of the others reach:
#       a session left open across a break. SessionStart fires once, at the
#       start; pre-write fires once, at the first write -- so a tab that has
#       been open for hours, and already made its first edit, is never
#       rechecked no matter how far origin moves underneath it.
#       This mode runs the session-start checks again, THROTTLED: it does
#       nothing at all unless the last check is older than the interval
#       (default 600s, `git config precedent.freshness.intervalSeconds` to
#       change). Nothing polls and nothing runs in the background -- the
#       hook only exists while a prompt is being submitted, and "idle" is
#       computed there and then by subtracting the stamp file's mtime from
#       now. Measured cost of the skipped path: ~8ms, almost all of it bash
#       starting up, no network, no output, so nothing enters the model's
#       context. The one prompt that pays the ~500ms fetch is the first one
#       back after a break -- exactly the prompt whose checkout might be
#       stale. ALWAYS exits 0: a UserPromptSubmit hook that exits non-zero
#       blocks the message, and losing what someone just typed over a
#       freshness question is far worse than the staleness.
#       ONE CHECK DOES NOT CARRY OVER FROM SESSION-START: the diverged-but-
#       clean auto-reconcile (rescue-ref then `git reset --hard`) is safe
#       only when nothing reachable from local HEAD can be this session's
#       own work yet, which is true at SessionStart and false here -- a
#       mid-session tab can hold a real unpushed commit. `_session_start_one`
#       tells the two apart by checking $MODE, so this mode reports a
#       divergence instead of resolving it (same as pre-write's identical-
#       looking branch). Cost of getting this wrong, 2026-09-20: a real
#       local commit discarded mid-session, recovered only because the
#       rescue ref and the reflog both happened to still have it -- see
#       gotchas/gotcha-2026-09-20-freshness-guard-s-user-prompt-mode-hard-resets-a-mid-sess.md.
#
#   freshness-guard.sh pre-write [BASE]
#       A PreToolUse hook. Runs its checks ONCE per session -- the first
#       tool call -- and then gets out of the way for the rest of it. On a
#       checkout it cannot vouch for, it exits 2, which is how a PreToolUse
#       hook refuses a tool call and hands its stderr back as the reason.
#
# BASE is the branch this one is meant to sit on top of -- "main" here,
# "precedent-beta-v01" in BestPractice. It is an explicit argument, passed
# in settings.json, on purpose: BestPractice's own configured default
# branch is NOT its base branch, so anything that asks git for the default
# would confidently get the wrong answer there. With no BASE argument the
# script asks git for origin's default and, failing that, SKIPS the base
# check with a note rather than guessing.
#
# WHY THE BASE CHECK EXISTS AT ALL (this is the part that catches the real
# incident). Comparing HEAD against origin/<the same branch name> answers
# "am I behind my own remote", and on a feature branch that is almost
# always "no" -- including on a container whose clone is five days and two
# hundred commits old, where the branch and its remote counterpart agree
# with each other perfectly and are both equally out of date. The question
# that actually catches that is "does my branch already contain everything
# on its base", which is what `merge-base --is-ancestor` answers.
#
# WHY THE FAST-FORWARD IS SAFE. It runs only when all four of: the fetch
# succeeded, the working tree is clean, the branch has nothing origin does
# not (so there is nothing of mine to lose), and there is genuinely
# something to move to. `merge --ff-only` under those conditions cannot
# lose work and cannot produce a conflict -- it either moves the ref or
# refuses. It is deliberately NOT a hard reset (throws away whatever the
# preconditions failed to notice), NOT a rebase (rewrites published
# history -- see BestPractice's no-rewrite-for-warnings), and NOT `git
# pull` (merges or rebases depending on config, and per BestPractice's own
# gotchas log, a pull run inside a checkout someone handed you is exactly
# how a session got silently moved onto the wrong branch mid-work).
#
# WHY IT CHECKS REPOSITORIES THE SESSION MERELY HAS ATTACHED. A hook fires
# for the project dir and nothing else, so an attached sibling clone runs none
# of its own freshness checking however correctly its guard is installed.
# PRECEDENT_FRESHNESS_ALSO names those repositories; see _also_entries. Unset,
# nothing about this script's behaviour changes.
#
# WHY THIS NEVER TOUCHES THE BASE BRANCH AUTOMATICALLY. Bringing origin/BASE
# into a feature branch is a real merge with real conflict potential -- the
# opposite of the fast-forward above, which is a no-op or nothing. The
# guard reports it and names the command; a person or an agent runs it
# deliberately.

set -uo pipefail

MODE="${1:-}"
BASE_ARG="${2:-}"

# The repository currently being checked. It STARTS as the project dir and is
# reassigned as the also-list below is walked, so every helper here keeps
# working unchanged against whichever repo is in hand.
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
ROOT="$PROJECT_ROOT"

_git() { git -C "$ROOT" "$@"; }

# WHY AN ENV VAR, AND NOT MORE HOOK WIRING. A hook fires for the project dir
# and nothing else, so a repository ATTACHED to a session rooted somewhere
# else -- `add_repo`, a SessionStart clone, a sibling clone a team practice
# source resolves to -- is never checked by its own guard, because its own
# settings.json is never read. That is not theoretical: a branch was cut from
# a stale main on 2026-09-11 while that repository's own guard sat installed
# and silent one directory away.
#
# The identity chain already solved the same shape, and this is deliberately
# the same answer: precedent_identity.py's rung 1 is PRECEDENT_COMMIT_*,
# checked before anything that needs a clone or a hook, precisely because
# environment variables follow a session into every repository it touches.
# PRECEDENT_FRESHNESS_ALSO is that rung for freshness.
#
#   PRECEDENT_FRESHNESS_ALSO="/path/to/repo=main;/path/to/other=beta-branch"
#
# Entries are `;`-separated, each `<path>=<base branch>`. The base is spelled
# out per entry for the same reason the hook takes it as an argument: it is
# not detectable, and a repo whose configured default branch is not its base
# branch is exactly where detection gets it wrong. An entry whose path is
# absent or is not a git repository is NOTED and skipped, never blocked on --
# a typo in a config value is not a stale checkout, and wedging every session
# over one would teach people to unset the variable.
#
# Unset, this is a no-op: the project dir is checked exactly as before.
_also_entries() {
  local raw="${PRECEDENT_FRESHNESS_ALSO:-}"
  [ -n "$raw" ] || return 0
  # `printf '%s'` leaves the final entry unterminated, and `read` returns
  # non-zero on an unterminated line -- so the loop body never ran for the LAST
  # entry, which for a single-entry variable meant it never ran at all. Caught
  # by a fixture, not by reading. The trailing newline is the fix.
  printf '%s\n' "$raw" | tr ';' '\n' | while IFS= read -r entry; do
    entry="$(printf '%s' "$entry" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
    [ -n "$entry" ] || continue
    printf '%s\n' "$entry"
  done
}

# Prints "path<TAB>base" for a usable entry; prints nothing and NOTEs when the
# entry names somewhere this guard cannot check.
_also_resolve() {
  local entry="$1" path base
  case "$entry" in
    *=*) path="${entry%%=*}"; base="${entry#*=}" ;;
    *)   echo "NOTE: freshness-guard: PRECEDENT_FRESHNESS_ALSO entry '$entry' has no '=<base branch>' -- SKIPPED (not checked). Spell the base out: <path>=<base>." >&2; return 1 ;;
  esac
  path="$(printf '%s' "$path" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  base="$(printf '%s' "$base" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  if [ -z "$path" ] || [ -z "$base" ]; then
    echo "NOTE: freshness-guard: PRECEDENT_FRESHNESS_ALSO entry '$entry' is missing a path or a base -- SKIPPED (not checked)." >&2
    return 1
  fi

  # NOTHING EXPANDS A PATH THAT ARRIVES IN A VARIABLE'S VALUE. bash substitutes
  # `~` and `$HOME` when it parses a word, never when it reads them back out of
  # a variable, so `~/precedent-individual` set in an environment reaches this
  # function as those literal characters and `git -C` looks for a directory
  # with a tilde in its name.
  #
  # $HOME is the case that matters and the reason this exists. An individual
  # practice source lives at $HOME/precedent-individual, and $HOME is not the
  # same on every container -- so an absolute path written on one of them
  # silently names nothing on the next. Measured 2026-09-11: this project's own
  # environment carried /home/user/precedent-individual while the clone was at
  # /root/precedent-individual, and the entry had been resolving to nothing,
  # every session, for its whole life. Expanding makes ONE value correct
  # everywhere, which is the only version of this that survives a fresh
  # container (practice: durable-fix).
  #
  # Done by explicit substitution rather than `eval`: this value is a path, not
  # a script, and eval on it would run whatever a mistyped entry happened to
  # contain. ${HOME} before $HOME, or the second pattern eats the first's
  # braces.
  case "$path" in
    '~') path="${HOME:-}" ;;
    '~/'*) path="${HOME:-}${path#\~}" ;;
  esac
  path="${path//\$\{HOME\}/${HOME:-}}"
  path="${path//\$HOME/${HOME:-}}"
  path="${path//\$\{CLAUDE_PROJECT_DIR\}/$PROJECT_ROOT}"
  path="${path//\$CLAUDE_PROJECT_DIR/$PROJECT_ROOT}"
  if [ "$path" = "$PROJECT_ROOT" ]; then
    # Already checked as the project dir; checking it twice would double every
    # warning and, in pre-write, block on the same finding twice.
    return 1
  fi
  if ! git -C "$path" rev-parse --git-dir >/dev/null 2>&1; then
    # The entry as WRITTEN is named alongside what it expanded to, because
    # the two differing is the whole diagnosis when a $HOME-relative value is
    # being read on a container whose $HOME is somewhere else.
    local as_written=""
    [ "$path" = "${entry%%=*}" ] || as_written=" (from '${entry%%=*}')"
    echo "NOTE: freshness-guard: PRECEDENT_FRESHNESS_ALSO names '$path'$as_written, which is not a git repository (or is not there) -- SKIPPED (not checked), not passed." >&2
    return 1
  fi
  printf '%s\t%s\n' "$path" "$base"
}

# `git rev-parse <missing-ref>` exits non-zero but PRINTS THE REF NAME on
# stdout, so `$(git rev-parse X) || fallback` binds a ref name where a hash
# belongs (BestPractice's gotchas log: this reached CI as a truncated ref
# name masquerading as a commit). Everything below that may be absent goes
# through --verify --quiet, which is silent and exits 1.
_have_ref() { _git rev-parse --verify -q "$1" >/dev/null 2>&1; }

_in_git() { _git rev-parse --git-dir >/dev/null 2>&1; }

# Is this branch simply absent from origin, rather than origin being
# unreachable? `git fetch origin <branch>` exits non-zero for BOTH, and
# treating them the same is what made pre-write refuse the first write of
# every new branch: a branch origin has never heard of has nothing to be
# behind, so there is no staleness to guard against.
#
# `ls-remote --exit-code` separates them: 0 means origin answered AND has
# the ref, 2 means origin answered and does not, anything else means the
# question could not be asked at all. Only the middle case is safe to wave
# through -- an unreachable origin still blocks, which is the whole point
# of this guard.
_branch_absent_from_origin() {
  _git ls-remote --exit-code --heads origin "$1" >/dev/null 2>&1
  [ "$?" = "2" ]
}

_current_branch() {
  local b
  b="$(_git symbolic-ref --quiet --short HEAD 2>/dev/null)" || return 1
  [ -n "$b" ] || return 1
  printf '%s' "$b"
}

_dirty() {
  [ -n "$(_git status --porcelain --untracked-files=no 2>/dev/null)" ]
}

# A single-branch clone -- what `add_repo` and `git clone --single-branch`
# both hand you -- carries exactly one refspec, so no origin/<other branch>
# ref is ever written and every comparison below silently has nothing to
# compare against. Local config only, idempotent, adds no commits.
_widen_refspec() {
  if ! _git config --get-all remote.origin.fetch 2>/dev/null | grep -q 'refs/heads/\*'; then
    _git config --add remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*' 2>/dev/null
  fi
}

_resolve_base() {
  if [ -n "$BASE_ARG" ]; then
    printf '%s' "$BASE_ARG"
    return 0
  fi
  local head_ref
  head_ref="$(_git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)" || return 1
  [ -n "$head_ref" ] || return 1
  printf '%s' "${head_ref#origin/}"
}

_is_shallow() {
  [ "$(_git rev-parse --is-shallow-repository 2>/dev/null)" = "true" ]
}

# `--depth` is only ever passed to a clone that is ALREADY shallow. Passing
# it to a full clone does not "limit the fetch" -- it truncates the
# repository into a shallow one, which is how a guard meant to make history
# more reliable would end up destroying the history every check below reads.
_fetch_base() {
  if _is_shallow; then
    _git fetch --quiet --depth=200 origin "$1" 2>/dev/null || \
      _git fetch --quiet origin "$1" 2>/dev/null || true
  else
    _git fetch --quiet origin "$1" 2>/dev/null || true
  fi
}

# Returns 0 when HEAD already contains everything on origin/BASE. Prints
# nothing. A caller must treat a non-zero return as "missing commits OR
# could not tell" and say which, because on a shallow clone git answers
# this question from a truncated graph: BestPractice's gotchas log records
# merge-base reporting no common ancestor for two branches that genuinely
# share one, purely because the fetch had not reached back far enough.
_contains_base() {
  _git merge-base --is-ancestor "origin/$1" HEAD >/dev/null 2>&1
}

_behind_base_count() {
  _git rev-list --count "HEAD..origin/$1" 2>/dev/null || printf '?'
}

# A shallow clone counts every commit back to its graft point as LOCAL, so a
# checkout that is merely behind reads as diverged -- and both modes below
# then decline to update it, which is the one outcome worse than either. Cost
# on 2026-09-13: a session ran a whole thread against a day-old tree, applying
# rules that had been superseded, and only found out when an unrelated command
# was blocked. Deepen once and recount before believing the counts.
# practice: durable-fix. See record/GOTCHAS.md#g12 for the merge-base shape of
# the same false negative.
_deepen_if_shallow() {
  _is_shallow || return 1
  _git fetch --quiet --deepen=500 origin "$1" 2>/dev/null && return 0
  # Some git policy hooks refuse --unshallow; a bounded deepen is tried first
  # for that reason, and a failure here is not fatal -- the caller keeps the
  # counts it already had and says they are approximate.
  _git fetch --quiet --unshallow origin "$1" 2>/dev/null && return 0
  return 1
}

# How far apart in TIME the two tips are, which is the quantity a person
# actually judges risk on: "132 commits behind" says nothing, "your copy is a
# day older than the tip" says everything. Both timestamps come from git, so
# nothing here depends on the container's clock.
# practice: no-invented-specifics.
_gap_seconds() {
  local mine theirs
  mine="$(_git log -1 --format=%ct HEAD 2>/dev/null)" || return 1
  theirs="$(_git log -1 --format=%ct "origin/$1" 2>/dev/null)" || return 1
  case "$mine$theirs" in ''|*[!0-9]*) return 1 ;; esac
  [ "$theirs" -gt "$mine" ] || { printf '0'; return 0; }
  printf '%s' "$((theirs - mine))"
}

# The limit past which "behind" stops being a note and becomes the headline.
# Declared in precedent.json rather than compiled in, because a threshold
# nobody decided is doctrine (practice: constants-are-risk-inputs). A repo
# with no declaration, or no python3 on the hook path, falls back to the
# engine default; `git config precedent.freshness.staleHours N` overrides
# both for one checkout.
_stale_hours() {
  local v
  v="$(_git config --get precedent.freshness.staleHours 2>/dev/null || true)"
  case "$v" in ''|*[!0-9]*) v="" ;; esac
  if [ -z "$v" ] && [ -n "$ROOT" ] && [ -f "$ROOT/precedent.json" ]; then
    v="$(python3 -c 'import json,sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    raise SystemExit(0)
h = d.get("stale_checkout_hours")
if isinstance(h, int) and h > 0:
    print(h)' "$ROOT/precedent.json" 2>/dev/null || true)"
  fi
  case "$v" in ''|*[!0-9]*) v=24 ;; esac
  printf '%s' "$v"
}

# One phrase, appended to every message that reports a checkout as behind, so
# the age travels with the count wherever the count is printed.
# practice: one-formatter-per-quantity.
_age_phrase() {
  local gap limit hours
  gap="$(_gap_seconds "$1")" || { printf ''; return 0; }
  [ "$gap" -gt 0 ] || { printf ''; return 0; }
  hours="$((gap / 3600))"
  limit="$(_stale_hours)"
  if [ "$hours" -ge "$limit" ]; then
    if [ "$hours" -ge 48 ]; then
      printf ' STALE: this copy is %s day(s) older than origin/%s, past the %sh limit -- treat it as out of date and deal with it before working.' "$((hours / 24))" "$1" "$limit"
    else
      printf ' STALE: this copy is %sh older than origin/%s, past the %sh limit -- treat it as out of date and deal with it before working.' "$hours" "$1" "$limit"
    fi
  elif [ "$hours" -ge 1 ]; then
    printf ' (This copy is %sh older than origin/%s; the limit is %sh.)' "$hours" "$1" "$limit"
  fi
}

# The whole idle test: one stat and a subtraction, no network, no daemon.
# Returns 0 when a check is due. Stamps on the way through, so a burst of
# prompts costs one check between them rather than one each.
_throttle_due() {
  local stamp interval age now
  interval="$(_git config --get precedent.freshness.intervalSeconds 2>/dev/null || true)"
  case "$interval" in ''|*[!0-9]*) interval=600 ;; esac
  [ "$interval" = "0" ] && return 0
  # --absolute-git-dir, not --git-dir: the latter answers RELATIVE to the
  # repo ("`.git`"), while this hook's own working directory is wherever the
  # harness launched it. The first version used --git-dir, so the stamp
  # resolved against the wrong directory, every write failed, and the
  # throttle silently never engaged -- it re-checked on every single prompt
  # while printing a path error. Caught by the throttle test below, not by
  # reading it.
  local gd
  gd="$(_git rev-parse --absolute-git-dir 2>/dev/null || true)"
  [ -n "$gd" ] || return 0
  stamp="$gd/precedent-last-freshness-check"
  now="$(date +%s)"
  if [ -f "$stamp" ]; then
    age=$(( now - $(stat -c %Y "$stamp" 2>/dev/null || echo 0) ))
    [ "$age" -lt "$interval" ] && return 1
  fi
  : > "$stamp" 2>/dev/null || true
  return 0
}

# ---------------------------------------------------------------------------
# session-start
# ---------------------------------------------------------------------------
# One repository, reported and never enforced. Returns 0 always, like the mode
# that calls it.
_session_start_one() {
  ROOT="$1"
  BASE_ARG="$2"
  _in_git || return 0
  _widen_refspec

  local branch
  branch="$(_current_branch)" || {
    echo "NOTE: freshness-guard: HEAD is detached in $ROOT -- no branch to check." >&2
    return 0
  }

  local fetched=1
  _git fetch --quiet origin "$branch" 2>/dev/null || fetched=0
  if [ "$fetched" -eq 0 ] && _branch_absent_from_origin "$branch"; then
    fetched=1
    echo "NOTE: freshness-guard: '$branch' does not exist on origin yet -- nothing to be behind. Checking it against the base branch only." >&2
  elif [ "$fetched" -eq 0 ]; then
    echo "WARN: freshness-guard: could not fetch origin/$branch -- freshness NOT verified. Everything below is measured against a possibly stale remote-tracking ref; a silent result here means 'not checked', never 'in sync'." >&2
  fi

  # TODO.md's shallow-clone-self-heal-hardening item, g37's third recurrence.
  # Used to run only when the counts already looked diverged (ahead != 0) --
  # which is exactly the case a shallow clone gets WRONG on its own, and left
  # a checkout that was merely shallow-and-behind with no second chance if
  # session-start.sh's own attempt had failed. _deepen_if_shallow returns fast
  # (its own first line is `_is_shallow || return 1`) when there is nothing to
  # do, so calling it unconditionally, before the counts below are trusted at
  # all, costs nothing on an already-complete clone.
  _deepen_if_shallow "$branch" || true
  if _is_shallow; then
    _shallow_marker="$(_git rev-parse --absolute-git-dir 2>/dev/null || true)"
    [ -n "$_shallow_marker" ] && [ -f "$_shallow_marker/PRECEDENT_SHALLOW_UNRESOLVED" ] && \
      echo "WARN: freshness-guard: this checkout is STILL shallow after session-start.sh's own two attempts and this guard's own retry -- treat history-reading tools (behavioral_replay.py, doc_lint's changed-files scope, precedent_check.py's tree checks) as unverified. Remedy by hand: git fetch --unshallow" >&2
  else
    _shallow_marker="$(_git rev-parse --absolute-git-dir 2>/dev/null || true)"
    [ -n "$_shallow_marker" ] && rm -f "$_shallow_marker/PRECEDENT_SHALLOW_UNRESOLVED" 2>/dev/null
  fi

  if _have_ref "origin/$branch"; then
    local behind ahead
    behind="$(_git rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo 0)"
    ahead="$(_git rev-list --count "origin/$branch..HEAD" 2>/dev/null || echo 0)"
    if [ "$behind" != "0" ]; then
      if _dirty; then
        echo "WARN: freshness-guard: '$branch' is $behind commit(s) behind origin/$branch, and the working tree has uncommitted changes -- NOT updating it automatically.$(_age_phrase "$branch") Commit or stash, then: git merge --ff-only origin/$branch" >&2
      elif [ "$ahead" != "0" ]; then
        if [ "$MODE" != "session-start" ]; then
          # mode_user_prompt delegates to mode_session_start (see its own
          # comment above), which means this branch runs mid-session too --
          # and mid-session, unlike true SessionStart, local HEAD really can
          # hold this session's own unpushed work. The auto-reconcile below
          # is only safe for the case its own comment describes (before the
          # session's first turn), so anything reached via a mode other than
          # `session-start` gets the report-only treatment mode_pre_write
          # already uses for the identical-looking case.
          # practice: durable-fix -- see
          # gotchas/gotcha-2026-09-20-freshness-guard-s-user-prompt-mode-hard-resets-a-mid-sess.md
          echo "WARN: freshness-guard: '$branch' has diverged from origin/$branch ($ahead local commit(s), $behind remote) -- NOT reconciling automatically (this check is running mid-session, not at SessionStart, so local HEAD may hold this session's own unpushed work).$(_age_phrase "$branch") Reconcile deliberately: commit or stash anything of yours, then merge or rebase onto origin/$branch yourself." >&2
        else
          # This is SessionStart, before this session's first turn -- nothing
          # reachable from local HEAD can be this session's own work yet, so a
          # diverged-but-CLEAN checkout here is safe to reconcile automatically,
          # unlike the identical-looking check in mode_pre_write (which runs
          # mid-session, where a local commit really could be this session's),
          # and unlike this same branch reached via mode_user_prompt, above.
          # "Do not discard either side" still holds: the old tip is kept under
          # a dedicated ref, never just left to reflog expiry, before origin's
          # history replaces it.
          local rescue_ref old_sha
          old_sha="$(_git rev-parse HEAD 2>/dev/null)"
          rescue_ref="refs/freshness-guard/pre-reset/${branch}-${old_sha:0:12}"
          if [ -n "$old_sha" ] && _git update-ref "$rescue_ref" "$old_sha" >/dev/null 2>&1 && \
             _git reset --hard "origin/$branch" >/dev/null 2>&1; then
            echo "NOTE: freshness-guard: '$branch' had diverged from origin/$branch ($ahead local commit(s), $behind remote) -- reconciled it to origin/$branch (SessionStart, before this session's first turn, so nothing local could be this session's own work). The old tip is kept at $rescue_ref ($old_sha); nothing was discarded.$(_age_phrase "$branch")" >&2
          else
            echo "WARN: freshness-guard: '$branch' has diverged from origin/$branch ($ahead local commit(s), $behind remote) -- could not reconcile it automatically (rescue ref or reset failed), so leaving it as-is.$(_age_phrase "$branch") Reconcile deliberately; do not discard either side." >&2
          fi
        fi
      elif [ "$fetched" -eq 0 ]; then
        echo "WARN: freshness-guard: '$branch' looks $behind commit(s) behind, but the fetch failed -- not acting on an unverified comparison.$(_age_phrase "$branch")" >&2
      else
        local before
        before="$(_git rev-parse HEAD 2>/dev/null)"
        if _git merge --ff-only "origin/$branch" >/dev/null 2>&1; then
          echo "NOTE: freshness-guard: fast-forwarded '$branch' $behind commit(s) to origin/$branch (working tree was clean, nothing local to lose). What moved:" >&2
          _git log --oneline "$before..HEAD" 2>/dev/null | sed 's/^/    /' >&2
        else
          echo "WARN: freshness-guard: '$branch' is $behind commit(s) behind origin/$branch and the fast-forward did not apply -- update it deliberately before working." >&2
        fi
      fi
    fi
  fi

  local base
  if base="$(_resolve_base)"; then
    if [ "$base" != "$branch" ]; then
      _fetch_base "$base"
      if _have_ref "origin/$base"; then
        if ! _contains_base "$base"; then
          local n caveat=""
          n="$(_behind_base_count "$base")"
          _is_shallow && caveat=" (shallow clone -- the count may be approximate, but the answer is not: fetch deeper if you need the exact number)"
          echo "WARN: freshness-guard: '$branch' is missing $n commit(s) from origin/$base$caveat. This is the stale-base case: the branch can be perfectly in sync with its own remote and still be built on an old base. Bring it up to date deliberately: git merge origin/$base" >&2
        fi
      fi
    fi
  else
    echo "NOTE: freshness-guard: no base branch given and origin/HEAD does not resolve -- base-branch check SKIPPED (not passed). Pass the base as the hook's second argument in .claude/settings.json." >&2
  fi

  return 0
}

# The project dir first, then every repository the session merely has
# ATTACHED. Always exits 0: this half reports, and a freshness question must
# never be the thing that wedges a session.
mode_session_start() {
  _session_start_one "$PROJECT_ROOT" "$BASE_ARG"
  local entry resolved path base
  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    resolved="$(_also_resolve "$entry")" || continue
    path="${resolved%%$'\t'*}"
    base="${resolved#*$'\t'}"
    echo "NOTE: freshness-guard: also checking attached repository $path (base $base)." >&2
    _session_start_one "$path" "$base"
  done <<EOF
$(_also_entries)
EOF
  exit 0
}

# ---------------------------------------------------------------------------
# pre-write
# ---------------------------------------------------------------------------

# Exit 2 is how a PreToolUse hook refuses the call and hands stderr back to
# the model as the reason.
_block() {
  echo "BLOCKED by freshness-guard (first tool call of this session): $1" >&2
  echo "Fix it and retry. A git command is never blocked by this guard, so the remedy above is always runnable. To override deliberately for this checkout: git config precedent.freshness.override true" >&2
  exit 2
}

mode_pre_write() {
  local payload="" session="" tool="" command=""
  payload="$(cat 2>/dev/null || true)"

  if [ -z "$payload" ]; then
    # An EMPTY payload is a different failure from a missing parser, and the
    # branch below used to swallow both -- so a session that got no payload
    # was told "no jq, no python3" with both installed and working, which
    # sends whoever reads it off installing tools that are already there.
    # Same fail-open verdict, an honest reason (practice: fail-gracefully).
    echo "NOTE: freshness-guard: the hook payload was empty -- pre-write check skipped, not passed. This is not a missing-parser problem; jq and python3 are not implicated." >&2
    exit 0
  fi

  if command -v jq >/dev/null 2>&1; then
    session="$(printf '%s' "$payload" | jq -r '.session_id // empty' 2>/dev/null || true)"
    tool="$(printf '%s' "$payload" | jq -r '.tool_name // empty' 2>/dev/null || true)"
    command="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null || true)"
  elif command -v python3 >/dev/null 2>&1; then
    local parsed
    parsed="$(printf '%s' "$payload" | python3 -c 'import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    raise SystemExit(1)
print(d.get("session_id") or "")
print(d.get("tool_name") or "")
print((d.get("tool_input") or {}).get("command") or "")' 2>/dev/null || true)"
    session="$(printf '%s\n' "$parsed" | sed -n '1p')"
    tool="$(printf '%s\n' "$parsed" | sed -n '2p')"
    command="$(printf '%s\n' "$parsed" | sed -n '3p')"
  else
    # FAIL OPEN, deliberately, and only here. Everywhere else this guard
    # fails closed, because a checkout it could not verify is exactly what
    # it exists to stop. But a guard that cannot read its own payload also
    # cannot recognise the git commands that are its own escape hatch, and
    # blocking on that would lock the session out of the only tools that
    # could clear the block. The session-start layer still ran.
    echo "NOTE: freshness-guard: no JSON parser available (no jq, no python3) -- pre-write check skipped, not passed." >&2
    exit 0
  fi

  # git is never blocked: every remedy this guard names, and the override
  # itself, is a git command. Gating those would be a deadlock, and a git
  # invocation is not the content change this guard is about.
  local bare
  bare="$(printf '%s' "$command" | sed 's/^[[:space:]]*//')"
  case "$bare" in
    git\ *|git) exit 0 ;;
  esac

  local key sentinel
  key="${session:-ppid-$PPID}"
  sentinel="${TMPDIR:-/tmp}/precedent-freshness-${key}"
  [ -f "$sentinel" ] && exit 0

  # THE RACE THIS CLOSES. `key` is keyed on session_id alone when one
  # resolves -- which is the normal case -- so every tool call in one turn
  # computes the SAME sentinel path. When the harness dispatches two calls
  # concurrently, both processes read `[ -f "$sentinel" ]` as false before
  # either has written it, and both fall through to `_pre_write_one`, which
  # runs `git fetch`/`--deepen` against the same `.git` directory at once.
  # Reproduced 2026-09-15: one of two parallel Bash calls blocked on a
  # false "diverged" reading (a shallow-clone artifact, record/GOTCHAS.md#g37)
  # while its sibling call, racing the same checkout, read the correct
  # counts and passed clean -- same session, same instant, two different
  # verdicts, because nothing serialized them. flock turns the race into a
  # queue: a second caller that has to wait re-checks the sentinel on
  # waking and, finding the first caller already finished it, exits clean
  # instead of repeating the same git work against a checkout the first
  # caller may have just changed. Held on an fd, not in a subshell, so a
  # later `_block`'s plain `exit 2` still releases it as the process exits
  # normally -- no explicit unlock needed, and no lock this script must
  # remember to drop on every exit path. Absent `flock` (non-Linux, or a
  # trimmed container), this falls back to the pre-existing race rather
  # than blocking the tool call outright -- a guard that cannot lock is not
  # a guard that must therefore refuse (practice: fail-gracefully).
  if command -v flock >/dev/null 2>&1; then
    # `2>/dev/null` on the `exec` line itself is the trap, not the fix: bash
    # applies an `exec` with no command's redirections to the CURRENT SHELL,
    # permanently -- not scoped to this statement -- so it would silence
    # every later `echo ... >&2` in the rest of this process for the rest of
    # its run, not just a failed lock open. Proven with a two-line repro
    # where a stderr line AFTER the function that ran `exec 2>/dev/null`
    # inside it also went missing. `flock`'s own `2>/dev/null` is a normal
    # external command's redirection and stays scoped to that command.
    exec 9>"${sentinel}.lock"
    flock -x -w 30 9 2>/dev/null
    [ -f "$sentinel" ] && exit 0
  fi

  _in_git || { : > "$sentinel"; exit 0; }

  if [ "$(_git config --get precedent.freshness.override 2>/dev/null || true)" = "true" ]; then
    echo "NOTE: freshness-guard: precedent.freshness.override is set for this checkout -- freshness NOT checked this session." >&2
    : > "$sentinel"
    exit 0
  fi

  _pre_write_one "$PROJECT_ROOT" "$BASE_ARG" "$sentinel"

  # Every ATTACHED repository, under the same enforcement. A session reads its
  # practices out of these, so working against a stale one is the same failure
  # as working against a stale project dir -- and the override above is
  # deliberately NOT re-read per repo: it is set on the checkout somebody chose
  # to stop guarding, and this loop must not let that decision silence a
  # different repository.
  local entry resolved path base
  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    resolved="$(_also_resolve "$entry")" || continue
    path="${resolved%%$'\t'*}"
    base="${resolved#*$'\t'}"
    _pre_write_one "$path" "$base" "$sentinel"
  done <<EOF
$(_also_entries)
EOF

  : > "$sentinel"
  exit 0
}

# One repository, enforced. Returns 0 when it is current; calls _block (which
# exits 2) when it is not. The sentinel is passed in rather than read from the
# caller's scope: bash would resolve it dynamically either way, and a helper
# that silently depends on a `local` two frames up breaks the moment anything
# else calls it.
_pre_write_one() {
  ROOT="$1"
  BASE_ARG="$2"
  local sentinel="$3"

  _in_git || return 0
  _widen_refspec

  local branch
  branch="$(_current_branch)" || return 0

  if ! _git fetch --quiet origin "$branch" 2>/dev/null; then
    if _branch_absent_from_origin "$branch"; then
      echo "NOTE: freshness-guard: '$branch' does not exist on origin yet -- nothing to be behind, so this call is not blocked on it. The base-branch check below still runs." >&2
    else
      _block "could not fetch origin/$branch, so this checkout's freshness could not be verified at all. A check that could not run is not a check that passed. Run: git fetch origin $branch"
    fi
  fi

  # Unconditional now, same reasoning as _session_start_one's copy of this
  # comment: a shallow-but-merely-behind checkout used to get no deepen
  # attempt here at all, only when the counts already looked diverged.
  _deepen_if_shallow "$branch" || true

  if _have_ref "origin/$branch"; then
    local behind ahead
    behind="$(_git rev-list --count "HEAD..origin/$branch" 2>/dev/null || echo 0)"
    ahead="$(_git rev-list --count "origin/$branch..HEAD" 2>/dev/null || echo 0)"
    if [ "$behind" != "0" ]; then
      if _dirty; then
        _block "'$branch' is $behind commit(s) behind origin/$branch and the working tree is dirty.$(_age_phrase "$branch") Commit or stash first, then: git merge --ff-only origin/$branch"
      elif [ "$ahead" != "0" ]; then
        _block "'$branch' has diverged from origin/$branch ($ahead local, $behind remote).$(_age_phrase "$branch") Reconcile it deliberately -- this guard will not choose a side for you."
      else
        local before
        before="$(_git rev-parse HEAD 2>/dev/null)"
        if _git merge --ff-only "origin/$branch" >/dev/null 2>&1; then
          : > "$sentinel"
          echo "freshness-guard fast-forwarded '$branch' $behind commit(s) to origin/$branch before this call. What moved:" >&2
          _git log --oneline "$before..HEAD" 2>/dev/null | sed 's/^/    /' >&2
          _block "the tree just changed underneath you. Re-read anything you had already read from it, then retry -- this guard will not run again this session."
        else
          _block "'$branch' is $behind commit(s) behind origin/$branch and the fast-forward did not apply. Update it deliberately."
        fi
      fi
    fi
  fi

  local base
  if base="$(_resolve_base)" && [ "$base" != "$branch" ]; then
    _fetch_base "$base"
    if _have_ref "origin/$base" && ! _contains_base "$base"; then
      local n
      n="$(_behind_base_count "$base")"
      _block "'$branch' is missing $n commit(s) from origin/$base -- it is in sync with its own remote and still built on a stale base, which is the case that keeps producing work against code that moved. Bring it up to date: git merge origin/$base"
    fi
  fi

  return 0
}

# Deliberately delegates to mode_session_start instead of restating its
# checks: this file already had two copies of "is this checkout current"
# living beside a third in .claude/hooks/session-start.sh, and a fourth
# would drift from the others the first time any one of them was fixed.
# The throttle is the only thing this mode adds.
mode_user_prompt() {
  _in_git || exit 0
  _throttle_due || exit 0
  mode_session_start
}

case "$MODE" in
  session-start) mode_session_start ;;
  user-prompt)   mode_user_prompt ;;
  pre-write)     mode_pre_write ;;
  *)
    echo "usage: freshness-guard.sh <session-start|user-prompt|pre-write> [base-branch]" >&2
    exit 0
    ;;
esac
