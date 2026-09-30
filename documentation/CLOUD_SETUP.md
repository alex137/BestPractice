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
PRECEDENT_PING=1          # throwaway: proves the variables arrive at all

# The zone your commits are stamped in
PRECEDENT_COMMIT_TZ=America/Argentina/Buenos_Aires   # an IANA zone name, never an offset
```

That is all most people need. **The account your token belongs to is where
your practice sets are looked for** (`https://github.com/<that account>/<set>`),
worked out once and kept in `~/.config/precedent/config.json`. Set
`PRECEDENT_SOURCE_BASE_URL=https://github.com/<account>` only if your sets
belong to a different account or an organization. **Your name and email**
come from your individual set's `identity.json`, or, without one, from
your GitHub account, and the session says which. **The practice sets your
project declares are checked for freshness on their own**;
`PRECEDENT_FRESHNESS_ALSO` is only for an extra repository nothing declares.

Once `PRECEDENT_GIT_TOKEN` is set, the
SessionStart hook clones your individual and shared practice sets **before
the first turn** and writes your `~/.config/precedent/config.json` itself —
there is nothing else to fill in by hand for a hosted session. The one field
nothing can resolve on its own is your timezone in that set's
`identity.json`; `PRECEDENT_COMMIT_TZ` above covers the same ground without
it.

**No individual set?** Set nothing from the first block. With no token, base
URL or repo name in the environment and no clone on disk, nothing could have
fetched a set, so a hosted session reads a missing one as "you have none"
and says nothing. If you reach your set some other way, such as attaching
it by hand, set `PRECEDENT_INDIVIDUAL_REPO` so a failed fetch is still
reported.

**A private shared set with no token?** Vendor its practices into the
consumer instead of resolving them from a sibling clone: set
`upstream.vendor_practices: true` in the consumer's
`process/manifest_<set>.json`, run `checkin.py update <clone> --source <set>`,
and point the source's `path` in `precedent.json` at `process/<set>`. Only in
a private consumer.

## Optional but Recommended: Run Each Repo's Startup Hooks

**Skip this and a session that opens across several repositories quietly
runs none of their startup hooks.** It is one paste into the environment's
setup script, done once per environment.

Claude Code runs the hooks of the folder a session is opened in. A session
that works across several repositories is opened in the folder that holds
them all (`/home/user`), which has no hooks of its own, so **none of the
repositories' SessionStart hooks run**: no commit identity, no practice list
from your own and your team's sets, no engine refresh. Nothing inside a
repository can fix this, because nothing inside one runs. A user-level hook
does run, wherever the session opens, and
[tools/precedent_run_session_hooks.py](../tools/precedent_run_session_hooks.py)
is what it calls: it runs each repository's own SessionStart hooks, and does
nothing in a session opened inside a repository.

Add this to the environment's **setup script** (the environment's settings,
under Setup script). It writes the user-level hook each time a container
starts, and only new sessions pick it up. `~` is `/root` on a hosted
container, so `~/.claude` is the user-level folder; written as
`/home/user/.claude` instead, it becomes the settings of the folder the
session opens in, which works just as well for a session opened there:

```sh
mkdir -p ~/.claude
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / '.claude' / 'settings.json'
d = json.loads(p.read_text()) if p.exists() else {}
cmd = ('f=$(ls -d /home/user/*/tools/precedent_run_session_hooks.py '
       '2>/dev/null | head -1); [ -n "$f" ] && python3 "$f" || true')
starts = d.setdefault('hooks', {}).setdefault('SessionStart', [])
if cmd not in json.dumps(starts):
    starts.append({'hooks': [{'type': 'command', 'command': cmd}]})
p.write_text(json.dumps(d, indent=2))
PY
```

**First added to a real environment on 2026-09-28, not yet confirmed in a
session started after it.** The runner itself was run by hand in a real
session opened in `/home/user` and ran all 25 hooks across six repositories;
whether the hosted harness reads the user-level settings the setup script
writes is what the next new session shows. In it,
`python3 tools/precedent_session_check.py` reports whether
`.precedent/SESSION_PRACTICES.md` exists and whether commits are authored by
you, and both are red when no hook ran.

If you do set `PRECEDENT_FRESHNESS_ALSO` for an extra repository,
`python3 tools/precedent_session_check.py` says whether each entry names a
repository that is there.

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

## Let a "Promote" Into `main` Through Claude Code's Safety Check

**Only if you run sessions in auto mode and want a plain "Promote" to
reach `main`.** Claude Code's auto mode has its own safety check, separate
from Precedent's rules, and it treats moving `staging` into `main` as a
production deploy. It lets that through only when your message names the
exact move, so **"Produce"** (or "Promote 5") works and a bare
**"Promote"** is stopped with `[Production Deploy]`. A session that hits
this says so in one line and asks you for "Produce"; it never tries to get
around the check
([promote](../practices/promote.md), [produce](../practices/produce.md)).

To make a plain "Promote" work too, add an **allow rule** for it. **A
session cannot do this for you**, and a repository cannot carry it: the
check ignores a project's own `.claude/settings.json`, and refuses a
session that tries to write the rule itself. Where it goes (Claude Code's
own docs, read 2026-09-30):

- **For cloud sessions:** your organization's **managed settings**, at
  [Admin Settings > Claude Code > Managed settings](https://claude.ai/admin-settings/claude-code).
  That needs a Claude Team or Enterprise plan and the Owner or Primary
  Owner role, and it applies to everyone in the organization. Settings on
  your own computer don't reach a cloud session.
- **For sessions on your own computer:** `~/.claude/settings.json`, or the
  **Auto mode** tab of `/permissions`.

Paste this in, keeping `"$defaults"`: **without it, the list replaces every
built-in exception**, not just adds one.

```json
{
  "autoMode": {
    "allow": [
      "$defaults",
      "Precedent Promote into main: running tools/precedent_branches.py --promote --to main is allowed when the person asked in this session for Promote, Produce or Promote 5. That tool moves main only through a pull request, after the full local check and the GitHub test pass."
    ]
  }
}
```

The rule is written in plain words because the check reads it as prose,
not as a pattern. On your own computer, `claude auto-mode config` shows
whether it took; a cloud session picks it up when it next starts. Details:
[Configure auto mode](https://code.claude.com/docs/en/auto-mode-config)
and [server-managed settings](https://code.claude.com/docs/en/server-managed-settings).
On a plan without managed settings, keep saying "Produce".

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
   is exactly what the hook exists to replace. Add it as a workflow of your
   own, say `.github/workflows/doc-lint.yml`, running
   `python3 tools/doc_lint.py` on `"**/*.md"`, and record your approval of it
   in `precedent.json`'s `github_ci_approved`, in your own words. Do not edit
   `light-check.yml` for this: since 2026-09-27 every "Update Vendors"
   writes that file back from upstream's template, and removes any workflow
   nobody approved.
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
