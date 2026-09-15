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
