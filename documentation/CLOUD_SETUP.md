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

## When the Container's Own Signing Collides With a Human-Only Policy

Claude Code Remote signs every commit with a key tied to
`noreply@anthropic.com`, **container-wide** (`commit.gpgsign=true` in
`/root/.gitconfig`, set fresh on every container) — that's how GitHub shows
a Claude-authored commit as Verified. **If the project, or your own
practices, also require every commit to carry a real person's identity, the
two collide on every single commit, forever**: the stop hook flags each one
as Unverified and recommends switching to the bot identity, and a
human-authorship guard immediately refuses that switch. Measured
2026-09-17: this fired on three consecutive commits in one session before
anyone traced why, on a repo whose own commit-identity backstop explicitly
refuses `noreply@anthropic.com` as an author by design.

**The fix has to survive a fresh container, so it belongs in whatever
script already runs at session start and already sets up your commit
identity** — not a one-off `git config` you'd have to repeat by hand every
session:

```sh
git config commit.gpgsign false
```

Add that line beside wherever your identity hook already does
`git config user.name` / `git config user.email` — for a repo running
Precedent's own commit-identity backstop, that's the hook installing it
(`commit-identity.sh`, or the session-start hook that calls it). It
overrides the container-wide default **for that one checkout only**, so the
stop hook's Unverified check (which only runs when `commit.gpgsign` reads
`true`) never fires there again, and the human-authorship guard never has
to refuse anything.

**Only do this where you actually want human-only authorship.** In a
repository where nobody minds a Claude-authored, GitHub-Verified commit,
the container's default is doing exactly what it's for — leave it alone
there.

## Keep the Checkout From Going Stale

A session's container can start from cached state instead of a genuinely
fresh clone. **Verified 2026-09-15:** one environment, running since
2026-04-17, had every session start from a container frozen at a single
commit days old — diverged from live origin — which then tripped the
freshness guard and the Stop hook on every session as if real unpushed work
existed. Recreating the environment cleared it that one time; whether the
same environment drifts again on a schedule is still open
([TODO.md's `check-default-cc-environment-staleness` item](../todo/todo-2026-09-15-check-default-cc-environment-staleness.md)).

Add a fetch-and-fast-forward to the environment's **Setup command** field — same
screen as the environment variables above — to bring the checkout current
on start whenever that is a fast-forward:

```sh
if git rev-parse --git-dir >/dev/null 2>&1; then
  b="$(git branch --show-current)"
  [ -n "$b" ] && git fetch origin "$b" && git merge --ff-only "origin/$b"
fi
```

Deliberately generic: no repo name, no branch name. It reads both from the
checkout it's run against, so the same line works whatever repository and
branch the environment happens to open — not just this one.

**The guard is load-bearing, not defensive padding.** A bare
`b="$(git branch --show-current)"; git fetch origin "$b" && git reset --hard "origin/$b"` (the form in use then)
errored the first time it was tried, 2026-09-15: the Setup command runs
before the checkout is ready, so `git branch --show-current` had nothing to
read yet. The `if`/`[ -n "$b" ]` guards make it a no-op on that run instead
of failing, and it confirmed working the same day once added.

**A fast-forward, never a reset (changed 2026-09-23).** This line used to
end in `git reset --hard "origin/$b"`, which forces the checkout onto
origin by throwing away whatever local commits it holds. That is the one
move the fresh-before-write practice rules out by name, and a setup script
is no exception: it cannot tell a stale cached commit from somebody's real
work. A checkout that is only behind is brought current here. One that has
genuinely diverged is left alone, and the freshness guard merges it at
session start, keeping both sides. **The cost, stated plainly:** if a cached
container really does carry stale commits origin never had, that merge
brings them back in, and they show up as unpushed work until someone
settles them by hand. Recreating the environment is still the clean fix for
that case.

**Still unconfirmed as of 2026-09-15: whether the Setup command re-runs on
every session start, or only once when the environment's image is built.**
If it's the latter, this stops helping after the image is built — verify by
starting two sessions a few days apart in the same environment and
comparing `git log -1`.

## If You Work Through Something Other Than Claude Code

**The Markdown check is a hook, and hooks need a shell.** As of 2026-09-21
the Markdown lint no longer runs in GitHub Actions at all — it was
re-running a check the session had already run. What replaced it is
`.claude/hooks/doc-lint-gate.sh`, which refuses a `git commit` whose
staged Markdown fails [doc_lint.py](../tools/doc_lint.py).

**That is a Claude Code mechanism, and only Claude Code runs it.** A
GitHub-connected ChatGPT conversation gets no interactive shell, and
[templates/harness/README.md](../templates/harness/README.md)'s adapter
table shows the other harnesses carrying `n/a` or an unverified lifecycle
hook. **On any of those, nothing is checking your Markdown before it
reaches the shared branch — not the hook, and not CI.**

If that is you, do both of these. Not one:

1. **Run it yourself before every commit:**
   `python3 tools/doc_lint.py <the markdown you touched>`. Your harness
   will not remind you and nothing will stop you forgetting.
2. **Put the GitHub check back on**, because step 1 is a habit and a habit
   is exactly what the hook exists to replace. Copy
   [templates/github-actions/light-check.yml.template](../templates/github-actions/light-check.yml.template)
   to `.github/workflows/light-check.yml`, set its `CUSTOMIZE` command to
   `python3 tools/doc_lint.py` and its `paths:` list to `"**/*.md"`.
3. **Enable Actions for the repository** at **Settings → Actions** if it is
   off. A workflow file sitting in a repository with Actions disabled is a
   check nobody runs, and nothing tells you it is not running.

**Doing only the first is the arrangement that just failed here.** "A
session is supposed to run the check before committing" was written down,
and followed, for months — and still nothing refused a commit that skipped
it. That was only ever safe because CI was behind it. On a harness with
less enforcement than the one that had that gap, the CI check is not
optional.

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
