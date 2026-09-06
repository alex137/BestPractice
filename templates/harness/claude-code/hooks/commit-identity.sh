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
#   2. The person's own INDIVIDUAL practice source, if one resolves:
#      $PRECEDENT_USER_CONFIG (or ~/.config/precedent/config.json) names its
#      path, and an identity.json at the root of that source declares
#      {"name", "email", "timezone"}. This is the architecturally right
#      answer -- a person's individual set is exactly where person-specific
#      facts belong, and a shared repo asking it is how the shared repo
#      avoids knowing anything about any particular person.
#   3. CCR_SESSION_ACCOUNT_EMAIL, when the harness provides the session
#      owner's address.
#   4. The GitHub account this session is authenticated as
#      (`https://api.github.com/user`), which is the literal answer to "the
#      GitHub user using it". Falls back to that account's
#      <id>+<login>@users.noreply.github.com when the profile email is
#      private.
#   5. An identity already configured locally, as long as it is not the
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
# WHAT IS ENFORCED, EVERYWHERE, BY THE pre-commit HOOK THIS INSTALLS: that
# the author is not the container's bot and is not empty. That one is safe
# to refuse on in any repository, under any person, because it is never
# what anybody meant.
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
fi
zone="${PRECEDENT_COMMIT_TZ:-}"
[ -n "$zone" ] && zone_source="PRECEDENT_COMMIT_TZ"

# --- 2. the individual practice source's own identity.json
if [ -z "$email" ] || [ -z "$zone" ]; then
  cfg="${PRECEDENT_USER_CONFIG:-$HOME/.config/precedent/config.json}"
  if [ -f "$cfg" ] && command -v python3 >/dev/null 2>&1; then
    resolved="$(python3 - "$cfg" <<'PY' 2>/dev/null || true
import json, pathlib, sys
try:
    cfg = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
    path = (cfg.get('individual') or {}).get('path')
    ident = json.loads((pathlib.Path(path) / 'identity.json').read_text(encoding='utf-8'))
except Exception:
    raise SystemExit(0)
print(ident.get('name') or '')
print(ident.get('email') or '')
print(ident.get('timezone') or '')
PY
)"
    if [ -n "$resolved" ]; then
      i_name="$(printf '%s\n' "$resolved" | sed -n '1p')"
      i_email="$(printf '%s\n' "$resolved" | sed -n '2p')"
      i_zone="$(printf '%s\n' "$resolved" | sed -n '3p')"
      if [ -z "$email" ] && [ -n "$i_email" ]; then
        name="$i_name"; email="$i_email"; source="the individual practice source's identity.json"
      fi
      if [ -z "$zone" ] && [ -n "$i_zone" ]; then
        zone="$i_zone"; zone_source="the individual practice source's identity.json"
      fi
    fi
  fi
fi

# --- 3. the harness's own record of the session owner
if [ -z "$email" ] && [ -n "${CCR_SESSION_ACCOUNT_EMAIL:-}" ]; then
  email="$CCR_SESSION_ACCOUNT_EMAIL"
  name="${email%%@*}"
  source="the session account's own address"
fi

# --- 4. the GitHub account this session is authenticated as
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

# --- 5. an identity already configured here, if it is not the bot's
if [ -z "$email" ]; then
  have_name="$(git -C "$ROOT" config --get user.name 2>/dev/null || true)"
  have_email="$(git -C "$ROOT" config --get user.email 2>/dev/null || true)"
  if [ -n "$have_email" ] && ! _is_bot "$have_email" "$have_name"; then
    name="$have_name"; email="$have_email"; source="the identity already configured in this checkout"
  fi
fi

if [ -z "$zone" ]; then
  zone="$DEFAULT_TZ"
  zone_source="default (nobody declared one)"
  zone_is_guess=1
else
  zone_is_guess=0
fi

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
  echo "WARN: commit-identity: could not work out who is running this session, from any of the five sources this hook knows. Commits will use whatever git is already configured with -- and the pre-commit backstop will refuse them if that is the container's own bot identity. Set PRECEDENT_COMMIT_NAME/PRECEDENT_COMMIT_EMAIL to settle it." >&2
fi

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

if [ "$zone_is_guess" -eq 1 ]; then
  cur_offset="$(date +%z 2>/dev/null || true)"
  guess_offset="$(TZ="$zone" date +%z 2>/dev/null || true)"
  if [ -n "$cur_offset" ] && [ -n "$guess_offset" ] && [ "$cur_offset" != "$guess_offset" ]; then
    echo "NOTE: commit-identity: no timezone is declared anywhere for this person, so commits will carry this container's offset ($cur_offset) rather than $zone ($guess_offset). Declare one in your individual source's identity.json, or set PRECEDENT_COMMIT_TZ, and it becomes enforced rather than assumed." >&2
  fi
fi

exit 0
