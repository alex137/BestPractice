# Cloud Setup — Precedent on Claude Code on the Web

**Most people run Precedent this way** — a hosted session on
[claude.ai/code](https://claude.ai/code), not a local checkout — so this page
is the fast path for that case: four settings, in one place, and you're done.
Working locally instead, or want every variable and what each one does?
[PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md) is the complete reference this
page is drawn from.

**Nothing here is required.** Precedent installs and runs with none of it
set — you just get the defaults in
[PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md#what-applies-until-you-set-any-of-it)
instead of your own name, timezone, and private practices. The one default
that is actually bad, and the reason to bother: without a token, your own and
your team's practices **silently never load**, and a session applies the
wrong rules all day with no way to tell.

## Where This Goes

Open [claude.ai/code](https://claude.ai/code), go to the environment this
project runs in, and find its **environment variables** — the exact screen
is in Anthropic's own guide at
[code.claude.com/docs/en/claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web),
worth checking directly if the layout has moved since it was last confirmed
there, 2026-09-11. Add each line below as its own variable, with your own
values substituted in.

```sh
# Reaching your private practice sets from a hosted session
PRECEDENT_GIT_TOKEN=github_pat_<your read-only token>
PRECEDENT_SOURCE_BASE_URL=https://github.com/<your-github-account>
PRECEDENT_PING=1          # throwaway: proves the variables arrive at all

# Who your commits are by, and in what zone
PRECEDENT_COMMIT_NAME=Your Name
PRECEDENT_COMMIT_EMAIL=you@example.com
PRECEDENT_COMMIT_TZ=America/Argentina/Buenos_Aires   # an IANA zone name, never an offset

# Only if a team practice source resolves as a sibling clone beside this
# project — skip it otherwise:
PRECEDENT_FRESHNESS_ALSO=~/precedent-individual=main
```

Once `PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL` are set, the
SessionStart hook clones your individual and team practice sets **before
the first turn** and writes your `~/.config/precedent/config.json` itself —
there is nothing else to fill in by hand for a hosted session. The one field
nothing can resolve on its own is your timezone in that set's
`identity.json`; `PRECEDENT_COMMIT_TZ` above covers the same ground without
it.

## Two Things That Each Cost a Day When Skipped

- **A change here never reaches a session that is already running.** Test
  it in a **new** session — a resumed one can report zero `PRECEDENT_*`
  variables even when they are set correctly, because it started before you
  set them.
- **An account can hold two environments with the same name**, and the
  values can end up on the one your sessions are not running in — with
  `env | grep -c PRECEDENT` reading as **0** either way. Give your
  environments distinct names, and the `PRECEDENT_PING=1` line above tells
  you, in a new session, whether the variables arrived at all before you
  start chasing the token itself.

## Keep the Checkout From Going Stale

A session's container can start from cached state instead of a genuinely
fresh clone. **Verified 2026-09-15:** one environment, running since
2026-04-17, had every session start from a container frozen at a single
commit days old — diverged from live origin — which then tripped the
freshness guard and the Stop hook on every session as if real unpushed work
existed. Recreating the environment cleared it that one time; whether the
same environment drifts again on a schedule is still open
([TODO.md's `check-default-cc-environment-staleness` item](todo/todo-2026-09-15-check-default-cc-environment-staleness.md)).

Add a fetch-and-reset to the environment's **Setup command** field — same
screen as the environment variables above — to force the checkout current
on start, regardless of the container's cached state:

```sh
if git rev-parse --git-dir >/dev/null 2>&1; then
  b="$(git branch --show-current)"
  [ -n "$b" ] && git fetch origin "$b" && git reset --hard "origin/$b"
fi
```

Deliberately generic: no repo name, no branch name. It reads both from the
checkout it's run against, so the same line works whatever repository and
branch the environment happens to open — not just this one.

**The guard is load-bearing, not defensive padding.** A bare
`b="$(git branch --show-current)"; git fetch origin "$b" && git reset --hard "origin/$b"`
errored the first time it was tried, 2026-09-15: the Setup command runs
before the checkout is ready, so `git branch --show-current` had nothing to
read yet. The `if`/`[ -n "$b" ]` guards make it a no-op on that run instead
of failing, and it confirmed working the same day once added.

**Still unconfirmed as of 2026-09-15: whether the Setup command re-runs on
every session start, or only once when the environment's image is built.**
If it's the latter, this stops helping after the image is built — verify by
starting two sessions a few days apart in the same environment and
comparing `git log -1`.

## Verify It Worked

In a new session, in this project:

```sh
env | grep -c PRECEDENT                      # not 0
python3 tools/precedent_source_credentials.py # OK
python3 tools/precedent_session_check.py      # each guarantee, by effect
```

Still not resolving, or want the leak-gate vocabulary layer, the optional
escape hatches, or `identity.json`'s other fields (pronouns, whether your
approval travels to a session you're not typing in)?
[PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md) covers all of it — this page is
only the part specific to a hosted session.
