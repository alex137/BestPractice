#!/bin/bash
# Claude Code adapter: SessionStart hook -- make a commit's author the
# HUMAN running the session, not the container's own bot identity, without
# anyone having to remember.
#
# practice: session-bootstrap
#
# THE PROBLEM. A hosted container asserts a GLOBAL git identity of its own
# agent account at every session start -- deliberately, so that its commit
# signatures verify -- and runs on a UTC clock. Any rule that says "commit
# as yourself" is then an instruction competing with a default, on every
# commit, forever. In one repository that produced six wrong-author commits
# in three days before anyone counted; five of them had to be exempted by
# SHA, because rewriting published history to fix them would have been
# worse than the mistake.
#
# WHAT THIS DOES NOT DO: name a person. This script is installed in shared
# repositories, so it resolves whoever is actually running the session,
# in this order, and stops at the first answer:
#
#   1. PRECEDENT_COMMIT_NAME / PRECEDENT_COMMIT_EMAIL / PRECEDENT_COMMIT_TZ
#      -- an explicit override, for anyone whose situation none of the rest
#      of this fits.
#   2. An identity.json in THIS repository's own root -- which means this
#      repository IS somebody's individual practice source, and is declaring
#      its owner. A source is then self-sufficient: it needs no user-level
#      config pointing at itself to know whose it is.
#   3. The person's own INDIVIDUAL practice source, if one resolves:
#      $PRECEDENT_USER_CONFIG (or ~/.config/precedent/config.json) names its
#      path, and an identity.json at the root of that source declares
#      {"name", "email", "timezone"}. This is the architecturally right
#      answer -- a person's individual set is exactly where person-specific
#      facts belong, and a shared repo asking it is how the shared repo
#      avoids knowing anything about any particular person.
#
#      identity.json IS THE ONE PLACE those three values live, for everyone.
#      Anything else that needs them -- a settings.json `env` block, a
#      mechanical check asserting who a repo's commits are authored by --
#      derives from it and is checked against it, rather than restating it
#      (practice: registry-source-of-truth).
#   4. CCR_SESSION_ACCOUNT_EMAIL, when the harness provides the session
#      owner's address.
#   5. The GitHub account this session is authenticated as
#      (`https://api.github.com/user`), which is the literal answer to "the
#      GitHub user using it". Falls back to that account's
#      <id>+<login>@users.noreply.github.com when the profile email is
#      private.
#   6. An identity already configured locally, as long as it is not the
#      container's own bot identity -- the one thing that is never a human.
#
# TIMEZONE, AND WHY IT IS THE ONLY THING GUESSED. Nothing in a GitHub
# profile says where someone is. So: an explicit override, else the
# individual source's declared timezone, else America/New_York as a stated
# default. THE DEFAULT IS NEVER ENFORCED -- a commit whose offset does not
# match a guess earns a warning, not a refusal. Only a timezone somebody
# actually declared is enforced, because only then is a mismatch evidence
# of anything.
#
# WHAT THE pre-commit HOOK THIS INSTALLS REFUSES. Everywhere, under any
# person: an author that is the container's bot, or empty. That one is
# always safe, because it is never what anybody meant. Additionally, when
# the identity came from a DECLARATION rather than an inference -- an
# explicit override, or an identity.json -- the exact declared author and
# the declared timezone. The line is the same in both halves: enforce what
# somebody wrote down, never what this hook worked out for itself.
#
# FAILS GRACEFULLY: always exits 0. A SessionStart hook that can take a
# session down over a git-config question is worse than the mistake it
# prevents. The pre-commit hook it installs is the only part that refuses,
# and only a commit, never a session, with an override in its own message.

set -uo pipefail

BOT_EMAIL="noreply@anthropic.com"
DEFAULT_TZ="America/New_York"

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1 || exit 0

name="" email="" zone="" source=""
# Whether the identity came from something a PERSON DECLARED (an explicit
# override, or an identity.json) rather than from something inferred about
# the environment (the session account, the authenticated GitHub account, an
# existing git config). Only a declaration is enforced -- see the header.
declared=0

_is_bot() {
  case "${1:-}" in
    *"$BOT_EMAIL"*) return 0 ;;
  esac
  [ "${2:-}" = "Claude" ]
}

# --- 1. explicit override
if [ -n "${PRECEDENT_COMMIT_EMAIL:-}" ]; then
  name="${PRECEDENT_COMMIT_NAME:-}"
  email="$PRECEDENT_COMMIT_EMAIL"
  source="PRECEDENT_COMMIT_* environment"
  declared=1
fi
zone="${PRECEDENT_COMMIT_TZ:-}"

# --- 2. this repository's OWN identity.json -- it is an individual source
_read_identity_file() {
  command -v python3 >/dev/null 2>&1 || return 1
  python3 - "$1" <<'PY' 2>/dev/null
import json, pathlib, sys
try:
    ident = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
except Exception:
    raise SystemExit(1)
print(ident.get('name') or '')
print(ident.get('email') or '')
print(ident.get('timezone') or '')
PY
}

_take_identity() {  # $1 = three lines, $2 = where it came from
  local i_name i_email i_zone
  i_name="$(printf '%s\n' "$1" | sed -n '1p')"
  i_email="$(printf '%s\n' "$1" | sed -n '2p')"
  i_zone="$(printf '%s\n' "$1" | sed -n '3p')"
  if [ -z "$email" ] && [ -n "$i_email" ]; then
    name="$i_name"; email="$i_email"; source="$2"; declared=1
  fi
  if [ -z "$zone" ] && [ -n "$i_zone" ]; then
    zone="$i_zone"
  fi
}

if [ -z "$email" ] || [ -z "$zone" ]; then
  if [ -f "$ROOT/identity.json" ]; then
    own="$(_read_identity_file "$ROOT/identity.json" || true)"
    [ -n "$own" ] && _take_identity "$own" "this repository's own identity.json -- it is an individual practice source"
  fi
fi

# --- 3. the individual practice source named by the user-level config
if [ -z "$email" ] || [ -z "$zone" ]; then
  cfg="${PRECEDENT_USER_CONFIG:-$HOME/.config/precedent/config.json}"
  if [ -f "$cfg" ] && command -v python3 >/dev/null 2>&1; then
    indiv="$(python3 - "$cfg" <<'PY' 2>/dev/null || true
import json, pathlib, sys
try:
    cfg = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
except Exception:
    raise SystemExit(0)
print((cfg.get('individual') or {}).get('path') or '')
PY
)"
    if [ -n "$indiv" ] && [ -f "$indiv/identity.json" ]; then
      resolved="$(_read_identity_file "$indiv/identity.json" || true)"
      [ -n "$resolved" ] && _take_identity "$resolved" "the individual practice source's identity.json"
    fi
  fi
fi

# --- 4. the harness's own record of the session owner
if [ -z "$email" ] && [ -n "${CCR_SESSION_ACCOUNT_EMAIL:-}" ]; then
  email="$CCR_SESSION_ACCOUNT_EMAIL"
  name="${email%%@*}"
  source="the session account's own address"
fi

# --- 5. the GitHub account this session is authenticated as
if [ -z "$email" ] && command -v curl >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  gh="$(curl -s --max-time 10 https://api.github.com/user 2>/dev/null | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    raise SystemExit(0)
login = d.get("login")
if not login:
    raise SystemExit(0)
print(d.get("name") or login)
print(d.get("email") or f"{d.get(chr(105)+chr(100), 0)}+{login}@users.noreply.github.com")
' 2>/dev/null || true)"
  if [ -n "$gh" ]; then
    name="$(printf '%s\n' "$gh" | sed -n '1p')"
    email="$(printf '%s\n' "$gh" | sed -n '2p')"
    source="the GitHub account this session is authenticated as"
  fi
fi

# --- 6. an identity already configured here, if it is not the bot's
if [ -z "$email" ]; then
  have_name="$(git -C "$ROOT" config --get user.name 2>/dev/null || true)"
  have_email="$(git -C "$ROOT" config --get user.email 2>/dev/null || true)"
  if [ -n "$have_email" ] && ! _is_bot "$have_email" "$have_name"; then
    name="$have_name"; email="$have_email"; source="the identity already configured in this checkout"
  fi
fi

if [ -z "$zone" ]; then
  zone="$DEFAULT_TZ"
  zone_is_guess=1
else
  zone_is_guess=0
fi

# ---- MAKE THE OFFSET RIGHT, rather than only refusing it afterwards
#
# The three mechanisms below this one all act AFTER git has already resolved
# an offset: the pre-commit backstop refuses the commit, and the
# settings.local.json derivation only takes effect from the next session,
# because the harness reads environment before hooks run. So on the session
# that most needs it -- a fresh container, first commit -- the person is told
# to retype `TZ="..." git commit ...` on every commit, and the honest
# question is why the wrong offset was allowed to be produced at all.
#
# git resolves a commit's offset from $TZ, and falls back to the SYSTEM zone
# when TZ is unset. The system zone is the one lever a hook can actually move
# mid-session that every later shell, every tool, and every `git merge` picks
# up with no cooperation from any of them. So point the system zone at the
# declared one and the wrong offset stops being produced at all.
#
# 2026-09-08, the measurement that produced this block: this container's
# system zone was Etc/UTC, TZ was unset in every tool shell, and
# .claude/settings.local.json already declared the right zone and was inert.
# Every commit therefore got +0000 and was refused by the backstop -- working
# as designed, and one layer too late. The same fix had already been made in
# one consuming repo's own bootstrap.sh a day earlier; it belongs here, where
# every repo gets it (practice: engine-plus-host-shims).
#
# ONLY A DECLARED ZONE. A guessed default (America/New_York, from the header)
# is never written to the machine: it is not enforced for exactly the same
# reason, and changing a container's clock on a guess is worse than a warning.
#
# NOT A REPLACEMENT FOR THE BACKSTOP. The system zone file may be read-only,
# an explicit TZ= in the environment still wins over it, and this hook does
# not run for a repository attached mid-session. The backstop stays the thing
# that refuses; this is the thing that means it rarely has to.
#
# PRECEDENT_LOCALTIME overrides which file is repointed. It exists so this
# block can be TESTED -- a test that had to write the machine's real clock
# file would either not be written or be written to skip, which is how a
# mechanism ends up with no coverage at all.
_set_system_timezone() {
  [ "$zone_is_guess" -eq 0 ] || return 0
  local want cur target
  want="/usr/share/zoneinfo/$zone"
  target="${PRECEDENT_LOCALTIME:-/etc/localtime}"
  if [ ! -f "$want" ]; then
    echo "NOTE: commit-identity: no zoneinfo file for the declared zone ($zone), so the system clock is left alone. Commits still need TZ=\"$zone\" git commit ..." >&2
    return 0
  fi
  cur="$(date +%z 2>/dev/null || true)"
  [ "$cur" = "$(TZ="$zone" date +%z 2>/dev/null || true)" ] && return 0
  if ln -sf "$want" "$target" 2>/dev/null; then
    echo "NOTE: commit-identity: the system timezone was $cur; set to $zone ($(TZ="$zone" date +%z)), from the declared identity. Commits in THIS session now carry the right offset with no TZ= prefix -- that is prevention, where the pre-commit backstop is only refusal." >&2
  else
    echo "WARN: commit-identity: the system timezone file is not writable, so this container stays on $cur while the declared zone is $zone. Every commit here needs TZ=\"$zone\" git commit ... until that changes; the pre-commit backstop will refuse the ones that forget." >&2
  fi
}
_set_system_timezone

# ---- set what was resolved, locally, only when it would change something
if [ -n "$email" ]; then
  cur_name="$(git -C "$ROOT" config --local --get user.name 2>/dev/null || true)"
  cur_email="$(git -C "$ROOT" config --local --get user.email 2>/dev/null || true)"
  if [ "$cur_email" != "$email" ] || { [ -n "$name" ] && [ "$cur_name" != "$name" ]; }; then
    [ -n "$name" ] && git -C "$ROOT" config --local user.name "$name" 2>/dev/null
    git -C "$ROOT" config --local user.email "$email" 2>/dev/null
    echo "NOTE: commit-identity: commits from this checkout will be authored as '${name:-$email}' <$email>, from $source." >&2
  fi
else
  echo "WARN: commit-identity: could not work out who is running this session, from any of the six sources this hook knows. Commits will use whatever git is already configured with -- and the pre-commit backstop will refuse them if that is the container's own bot identity. Set PRECEDENT_COMMIT_NAME/PRECEDENT_COMMIT_EMAIL to settle it." >&2
fi

# ---- the SAME identity, GLOBALLY -- the half that reaches a repo which does
#      not exist yet
#
# THE FAILURE THIS CLOSES, THREE TIMES OVER. Everything above configures ONE
# checkout, at session start. A repository attached mid-session -- with
# `add_repo`, or cloned, or `git init`ed during the turn -- was never seen by
# that pass and inherits the container's GLOBAL identity instead, which is
# the agent bot account. So the repo-local fix cannot, even in principle,
# cover the case that keeps producing wrong-author commits. Measured
# 2026-09-07, not assumed: `git config --global user.email` read
# `noreply@anthropic.com`, and a repository created seconds later committed
# as `Claude <noreply@anthropic.com>` with no warning.
#
# Setting the resolved identity globally covers every repository the session
# will ever touch, including the ones it has not attached yet. It is the
# difference between fixing N checkouts and fixing the default they all fall
# back to.
#
# ONLY A DECLARED IDENTITY IS WRITTEN GLOBALLY. An identity this hook merely
# INFERRED -- from the authenticated GitHub account, say -- is a guess, and a
# guess written into global config would follow the user into every unrelated
# repository on the machine. A declaration (an identity.json, or an explicit
# PRECEDENT_COMMIT_* override) is somebody's stated answer to "who am I", and
# is safe to make the default.
#
# The bot identity is never treated as a thing worth preserving: it is what
# is being displaced.
_set_global_identity() {
  [ "$declared" -eq 1 ] || return 0
  [ -n "$email" ] || return 0
  local g_name g_email
  g_name="$(git config --global --get user.name 2>/dev/null || true)"
  g_email="$(git config --global --get user.email 2>/dev/null || true)"
  if [ "$g_email" = "$email" ] && [ "$g_name" = "$name" ]; then
    return 0                      # already right: no churn, no message
  fi
  [ -n "$name" ] && git config --global user.name "$name" 2>/dev/null
  git config --global user.email "$email" 2>/dev/null
  if _is_bot "$g_email" "$g_name"; then
    echo "NOTE: commit-identity: the GLOBAL git identity was the container's own agent account ($g_email). Set to '${name:-$email}' <$email>, so a repository attached or cloned LATER in this session inherits a person rather than the bot -- which is the gap a per-checkout fix cannot close." >&2
  else
    echo "NOTE: commit-identity: global git identity set to '${name:-$email}' <$email>, so repositories attached later in this session inherit it." >&2
  fi
}
_set_global_identity

# ---- the pre-commit backstop
gp="$(git -C "$ROOT" rev-parse --git-path hooks 2>/dev/null || true)"
[ -n "$gp" ] || exit 0
case "$gp" in
  /*) hooks_dir="$gp" ;;
   *) hooks_dir="$ROOT/$gp" ;;
esac
mkdir -p "$hooks_dir" 2>/dev/null || true
target="$hooks_dir/pre-commit"
marker="# precedent:commit-identity"

# Never clobber a pre-commit hook somebody else put here. Ours is
# recognised by its marker; anything else is left alone, out loud.
if [ -e "$target" ] && ! grep -q "$marker" "$target" 2>/dev/null; then
  echo "WARN: commit-identity: $target already exists and is not this one -- leaving it alone. The author backstop is NOT installed in this checkout." >&2
  exit 0
fi

expected_offset=""
if [ "$zone_is_guess" -eq 0 ]; then
  expected_offset="$(TZ="$zone" date +%z 2>/dev/null || true)"
fi
expected_name="" expected_email=""
if [ "$declared" -eq 1 ]; then
  expected_name="$name"
  expected_email="$email"
fi

cat > "$target" <<HOOK
#!/bin/sh
$marker -- installed by the commit-identity SessionStart hook; safe to
# delete, it is rewritten at every session start.
#
# \`git var GIT_AUTHOR_IDENT\` is the identity git is ABOUT to record, with
# config, environment and TZ already resolved -- so this checks the value,
# not the settings that were supposed to produce it.
set -u

[ "\${PRECEDENT_ALLOW_ANY_AUTHOR:-}" = "1" ] && exit 0

ident="\$(git var GIT_AUTHOR_IDENT 2>/dev/null || true)"
[ -n "\$ident" ] || exit 0

name="\${ident%% <*}"
rest="\${ident#*<}"
email="\${rest%%>*}"
offset="\${ident##* }"

# REFUSED, always: the container's own bot identity, which is never a
# human, and an empty author.
case "\$email" in
  *$BOT_EMAIL*)
    echo "commit refused: it would be authored by the container's own agent account (\$email), not by a person." >&2
    echo "  git config user.name 'Your Name' && git config user.email 'you@example.com'" >&2
    echo "  (or start a session with the SessionStart hook that resolves this automatically)" >&2
    echo "  Deliberate override, for one commit: PRECEDENT_ALLOW_ANY_AUTHOR=1 git commit ..." >&2
    exit 1
    ;;
esac
if [ -z "\$email" ] || [ -z "\$name" ]; then
  echo "commit refused: the author name or email is empty." >&2
  exit 1
fi

# Enforced only where somebody DECLARED an identity (an identity.json, or
# an explicit override). Where this hook merely inferred one -- from the
# authenticated GitHub account, say -- a different author is not evidence
# of a mistake, so it passes.
expected_name="$expected_name"
expected_email="$expected_email"
if [ -n "\$expected_email" ] && { [ "\$email" != "\$expected_email" ] || [ "\$name" != "\$expected_name" ]; }; then
  echo "commit refused: author is '\$name' <\$email>, but the declared identity is '\$expected_name' <\$expected_email>." >&2
  echo "  git config user.name '\$expected_name' && git config user.email '\$expected_email'" >&2
  echo "  Deliberate override, for one commit: PRECEDENT_ALLOW_ANY_AUTHOR=1 git commit ..." >&2
  exit 1
fi

# The timezone is enforced ONLY when somebody actually declared one.
# A default is a guess, and refusing a commit on a guess would be enforcing
# something this hook made up.
expected_offset="$expected_offset"
if [ -n "\$expected_offset" ] && [ "\$offset" != "\$expected_offset" ]; then
  echo "commit refused: author-date offset is '\$offset', but the declared timezone ($zone) is '\$expected_offset'." >&2
  echo "  TZ=\"$zone\" git commit ..." >&2
  echo "  Deliberate override, for one commit: PRECEDENT_ALLOW_ANY_AUTHOR=1 git commit ..." >&2
  exit 1
fi
exit 0
HOOK
chmod +x "$target" 2>/dev/null || true

# ---- the SAME backstop, wired for MERGE commits
#
# git does NOT run pre-commit for a merge commit. It runs prepare-commit-msg
# instead, and a non-zero exit there aborts the commit just the same. So the
# hook above -- the layer this script exists to provide -- was silent on the
# one commit kind nobody types by hand.
#
# practice: buenos-aires-dates, and cite-the-incident. Reproduced 2026-09-07
# in a throwaway clone with the pre-commit hook installed: `TZ=UTC git merge
# side` produced a merge commit dated +0000 and the hook never fired. That
# is not hypothetical -- it is how commit d85fcc9 reached this repo's own
# main an hour earlier, from a session that had been careful to run every
# `git commit` under the right TZ and had not thought about `git merge`.
#
# The hook body ignores its arguments, so the same file serves both roles
# (prepare-commit-msg is handed a message path, a source and a sha; this one
# reads only `git var GIT_AUTHOR_IDENT`, which is already resolved by then).
# Same marker, so the same never-clobber rule applies.
merge_target="$hooks_dir/prepare-commit-msg"
if [ -e "$merge_target" ] && ! grep -q "$marker" "$merge_target" 2>/dev/null; then
  echo "WARN: commit-identity: $merge_target already exists and is not this one -- leaving it alone. MERGE commits are NOT backstopped in this checkout." >&2
else
  cp "$target" "$merge_target" 2>/dev/null && chmod +x "$merge_target" 2>/dev/null || true
fi

# ---- make the DECLARED timezone the session's own, not a thing to retype
#
# The pre-commit backstop above refuses a commit whose offset contradicts a
# declared timezone. That is correct and it is not enough: a hook cannot
# export TZ into the shells a session runs later, so the person is told the
# remedy (`TZ="..." git commit ...`) and then types it on every commit,
# forever. 2026-09-07, the incident that produced this block: a session had
# been running under exactly that arrangement all day, and the complaint was
# the right one -- "I'd rather a permanent fix than my having to do that
# manually."
#
# So the resolved zone is written where the harness reads environment for the
# WHOLE session: .claude/settings.local.json's `env` block. That file is
# per-machine and untracked, which is what makes this safe in a SHARED repo --
# .claude/settings.json is committed and must not carry one contributor's
# zone (this repo's own settings.json comment says exactly that), while
# settings.local.json is that contributor's alone.
#
# registry-source-of-truth: identity.json stays the ONE place the zone is
# declared, and this block DERIVES the env from it at every session start,
# overwriting a stale value rather than treating it as a second declaration.
#
# It takes effect from the NEXT session -- environment is read before hooks
# run -- so this session still gets the refusal and the remedy line. Said out
# loud below rather than left to be discovered.
_derive_session_tz() {
  [ "$zone_is_guess" -eq 0 ] || return 0        # never propagate a guess
  command -v python3 >/dev/null 2>&1 || return 0
  python3 - "$ROOT/.claude/settings.local.json" "$zone" <<'DERIVE_TZ' 2>/dev/null
import json, pathlib, sys
path, zone = pathlib.Path(sys.argv[1]), sys.argv[2]
try:
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not isinstance(data, dict):
        raise SystemExit(0)
except Exception:
    # An unparseable settings.local.json is somebody's problem to fix, not
    # this hook's to overwrite. Say nothing and change nothing.
    raise SystemExit(0)
env = data.get('env')
if not isinstance(env, dict):
    env = {}
if env.get('TZ') == zone:
    raise SystemExit(0)                          # already right: no churn
env['TZ'] = zone
data['env'] = env
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
print('written')
DERIVE_TZ
}

if [ "$(_derive_session_tz)" = "written" ]; then
  echo "NOTE: commit-identity: wrote TZ=$zone into $ROOT/.claude/settings.local.json (untracked, per-machine), derived from the declared identity. It applies from the NEXT session on -- environment is read before hooks run -- so commits in THIS session may still need TZ=\"$zone\" git commit ..." >&2
  if ! git -C "$ROOT" check-ignore -q .claude/settings.local.json 2>/dev/null; then
    echo "WARN: commit-identity: .claude/settings.local.json is NOT gitignored here. It is a per-machine file, and committing it would push one person's timezone onto everyone -- add it to .gitignore." >&2
  fi
fi

# ---- the SAME backstop, GLOBALLY, for repositories that do not exist yet
#
# Global identity (above) fixes the DEFAULT a new repository inherits. This
# fixes the case where something overrides that default anyway -- a repo
# carrying its own stale `user.email`, a tool setting one, a clone that
# arrives pre-configured. A hook installed into one checkout cannot fire in a
# repository attached ten minutes later; `core.hooksPath` is the only setting
# that reaches all of them at once, including the ones not created yet.
#
# CHAINING IS NOT OPTIONAL. `core.hooksPath` makes git look THERE AND NOWHERE
# ELSE, so a global hooks directory silently disables every repository's own
# `.git/hooks/*`. That would be a worse bug than the one being fixed -- a
# repo's own pre-commit gate vanishing without a word. So each hook here runs
# the repository's own hook of the same name first, when it has one, and
# refuses if that one refuses.
#
# Skipped entirely if core.hooksPath is already set to something else: that is
# somebody's deliberate configuration, and stealing it is exactly the silent
# override this block exists to avoid.
_install_global_backstop() {
  [ "$declared" -eq 1 ] || return 0
  local dir existing
  dir="${PRECEDENT_GLOBAL_HOOKS:-$HOME/.config/precedent/git-hooks}"
  existing="$(git config --global --get core.hooksPath 2>/dev/null || true)"
  if [ -n "$existing" ] && [ "$existing" != "$dir" ]; then
    echo "NOTE: commit-identity: global core.hooksPath is already set to '$existing' -- leaving it alone. The global commit backstop is NOT installed; a repository attached later is protected by the global identity above, but nothing will refuse a wrong author there." >&2
    return 0
  fi
  mkdir -p "$dir" 2>/dev/null || return 0

  for hook in pre-commit prepare-commit-msg; do
    cat > "$dir/$hook" <<GLOBALHOOK
#!/bin/sh
$marker -- GLOBAL backstop, installed by the commit-identity hook.
# Reaches every repository on this machine, including ones attached or
# cloned after the session started -- the case a per-checkout hook cannot
# cover. Safe to delete; it is rewritten at every session start.
set -u

# The repository's OWN hook of this name still runs, and still decides.
# core.hooksPath would otherwise disable it silently.
# NOT \`rev-parse --git-path hooks\`: that RESPECTS core.hooksPath, so once
# this backstop is installed it resolves to the global directory and the
# repository's own hook is never found. Ask for the git dir itself.
_gitdir="\$(git rev-parse --absolute-git-dir 2>/dev/null || true)"
_own="\$_gitdir/hooks/$hook"
if [ -x "\$_own" ] && ! grep -q "$marker" "\$_own" 2>/dev/null; then
  "\$_own" "\$@" || exit \$?
fi

[ "\${PRECEDENT_ALLOW_ANY_AUTHOR:-}" = "1" ] && exit 0

ident="\$(git var GIT_AUTHOR_IDENT 2>/dev/null || true)"
[ -n "\$ident" ] || exit 0
name="\${ident%% <*}"
rest="\${ident#*<}"
email="\${rest%%>*}"
offset="\${ident##* }"

case "\$email" in
  *$BOT_EMAIL*)
    echo "commit refused: it would be authored by the container's own agent account (\$email), not by a person." >&2
    echo "  This is the GLOBAL backstop -- it fires in every repository, including one attached mid-session." >&2
    echo "  git config user.name '$name' && git config user.email '$email'" >&2
    echo "  Deliberate override, for one commit: PRECEDENT_ALLOW_ANY_AUTHOR=1 git commit ..." >&2
    exit 1
    ;;
esac
if [ -z "\$email" ] || [ -z "\$name" ]; then
  echo "commit refused: the author name or email is empty." >&2
  exit 1
fi

expected_offset="$expected_offset"
if [ -n "\$expected_offset" ] && [ "\$offset" != "\$expected_offset" ]; then
  echo "commit refused: author-date offset is '\$offset', but the declared timezone ($zone) is '\$expected_offset'." >&2
  echo "  TZ=\"$zone\" git commit ..." >&2
  echo "  Deliberate override, for one commit: PRECEDENT_ALLOW_ANY_AUTHOR=1 git commit ..." >&2
  exit 1
fi
exit 0
GLOBALHOOK
    chmod +x "$dir/$hook" 2>/dev/null || true
  done

  if [ "$existing" != "$dir" ]; then
    git config --global core.hooksPath "$dir" 2>/dev/null && \
      echo "NOTE: commit-identity: installed a GLOBAL commit backstop at $dir (core.hooksPath). It refuses a bot-authored or wrong-timezone commit in EVERY repository, including ones attached after this session started, and chains to each repository's own hook of the same name rather than replacing it." >&2
  fi
}
_install_global_backstop

if [ "$zone_is_guess" -eq 1 ]; then
  cur_offset="$(date +%z 2>/dev/null || true)"
  guess_offset="$(TZ="$zone" date +%z 2>/dev/null || true)"
  if [ -n "$cur_offset" ] && [ -n "$guess_offset" ] && [ "$cur_offset" != "$guess_offset" ]; then
    echo "NOTE: commit-identity: no timezone is declared anywhere for this person, so commits will carry this container's offset ($cur_offset) rather than $zone ($guess_offset). Declare one in your individual source's identity.json, or set PRECEDENT_COMMIT_TZ, and it becomes enforced rather than assumed." >&2
  fi
fi

exit 0
