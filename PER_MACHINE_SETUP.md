# Per-Machine Setup — What Each Person Sets, on Each Machine

[INSTALL.md](INSTALL.md) installs Precedent into a *repository*, once. This
page is the other axis: the settings that belong to **a person on a
computer**, and therefore have to be set again on every machine they work
from. **None of it lives in any repository** — that is the point of it — so
nothing in a fresh clone will remind you, and **most of it fails quietly
when absent.**

Written down because it kept being rediscovered. On 2026-09-07 a session
found the individual source's clone URL living in a public repository's
tracked hook, moved it to the private per-person config where it belongs,
and then had nowhere to say so.

## Copy-Paste Setup

**The whole of this page, as four blocks to paste and edit.** Everything
below this section explains what each one does and what breaks without it;
if you just want it working, these are enough.

**1. Your environment variables.** On Claude Code on the web, these go in
the environment's own configuration; locally, in your shell profile
(`~/.bashrc`, `~/.zshrc`). Replace the four bracketed values.

```sh
# Reaching your private practice sets from a hosted session
export PRECEDENT_GIT_TOKEN="github_pat_<your read-only token>"
export PRECEDENT_SOURCE_BASE_URL="https://github.com/<your-github-account>"
export PRECEDENT_PING=1          # throwaway: proves the variables arrive at all

# Who your commits are by, and in what zone
export PRECEDENT_COMMIT_NAME="<Your Name>"
export PRECEDENT_COMMIT_EMAIL="<you@example.com>"
export PRECEDENT_COMMIT_TZ="America/New_York"   # an IANA zone name, never an offset

# Freshness-check repositories your project's own hooks never reach.
# Write `~/name`, never a spelled-out path: $HOME differs between containers.
export PRECEDENT_FRESHNESS_ALSO="~/precedent-individual=main"
```

**2. Your user-level config**, at `~/.config/precedent/config.json` — the
file that tells every tool where your individual practice set lives. Never
in a shared project's tracked files.

```sh
mkdir -p ~/.config/precedent && cat > ~/.config/precedent/config.json <<'JSON'
{
  "format_version": 1,
  "individual": {
    "name": "precedent-individual",
    "path": "<absolute path to your local clone>",
    "repo_url": "https://github.com/<your-github-account>/precedent-individual"
  }
}
JSON
```

**3. Your `identity.json`**, inside your individual set. **Fill in the
timezone** — it is the field that fails silently, because name and email
resolve from the GitHub account the session is authenticated as and a zone
resolves from nowhere.

```json
{
  "format_version": 1,
  "name": "Your Name",
  "email": "you@example.com",
  "timezone": "America/New_York",
  "pronouns": "they/them",
  "grandfathered_commit_shas": []
}
```

**4. The leak gate's vocabulary layer**, if your private sources resolve.
The git config is per checkout and the gate fails open without it.

```sh
git config precedent.requireVocabulary true
# Optional — only if your blocklist lives somewhere other than your
# individual set, which the gate now reads by default:
export PRECEDENT_LEAK_BLOCKLIST="$HOME/precedent-individual/leak-blocklist.txt"
```

**Then check it worked, in a NEW session** — an environment change never
reaches one already running:

```sh
env | grep -c PRECEDENT                      # not 0
python3 tools/precedent_source_credentials.py # OK
python3 tools/precedent_session_check.py      # each guarantee, by effect
env -u GIT_AUTHOR_NAME -u GIT_AUTHOR_EMAIL -u TZ git var GIT_AUTHOR_IDENT
#   ^ must name you and your declared offset, not the bot and not UTC
```

## Required, and Silent When Missing

| Setting | Where | What happens without it |
|---|---|---|
| `individual.name`, `individual.path`, `individual.repo_url` | `~/.config/precedent/config.json` (or wherever `PRECEDENT_USER_CONFIG` points) | Your individual practices do not resolve. The session says so on stderr and runs with team and universal only — easy to miss in a long startup. `repo_url` specifically is what the session-start hook clones from; without it the hook cannot fetch your set. |
| `PRECEDENT_LEAK_BLOCKLIST` **and** `git config precedent.requireVocabulary true` | shell profile, and git config per checkout | The leak gate's vocabulary layer **fails open**: it prints `PARTIAL`, exits 0, and the push goes through with only the structural rules applied. Both are needed — the variable alone is not enough. **Since 2026-09-12 the variable is an override rather than the only route**: with it unset, the gate reads `leak-blocklist.txt` from the individual set your config names — the path this same section tells you to put it at — so a fresh shell no longer silently drops to the structural half. Set it anyway when your list lives somewhere else. |
| `# visibility-audit: private-owner <your GitHub account> -- reason`, inside that blocklist file | the private blocklist itself | Switches the **repo-reference allowlist** on. Without it, every `<account>/<name>` mention passes: a blocklist blocks only the names someone remembered, and a private repository you create tomorrow is not one of them. With it, each mention is refused until an `allow` line gives a reason. The gate prints `INERT` on every run until you declare it, rather than passing quietly. **Do not pre-allow your individual source** — a shared repo naming one is refused by [tools/precedent_resolve.py](tools/precedent_resolve.py) as a privacy boundary, so an allow line for it grants exactly what the architecture withholds. Two further directives live in the same file, both off by default and both dated 2026-09-12: `stem-notes off -- reason` moves the routine missing-stem note out of every push run and into the very deep check, and `auto-cover-bare-names on -- reason` makes each private clone's **bare** name a pattern in its own right, so the short form is refused without anybody writing a stem. |
| `name`, `email`, `timezone` in your individual set's `identity.json` | the individual set itself | Your commits carry the wrong person or the wrong clock. Name and address can still be resolved from the GitHub account the session is authenticated as, so this half often *looks* fine; **the timezone cannot be resolved from anywhere** — nothing in a GitHub profile says where a person is and a container's clock is UTC — so an unfilled zone silently downgrades the author-date check from enforced to guessed, and wrong-offset commits reach the remote before anyone notices. Use an Internet Assigned Numbers Authority (IANA) zone name (`America/New_York`), never a bare offset. The same file's `grandfathered_commit_shas` is the exemption list for commits that were **already published** when a violation surfaced; it starts empty and stays empty until you genuinely need one — an unpushed commit gets fixed, not listed. |
| `pip install cmarkgfm markdown` | the machine | `doc_lint.py`'s strikethrough check stops running and says so in one line, and `doc_html.py` cannot import. A session-start hook installs these where one runs; a repo attached mid-session never runs its own hook, so do it by hand there. |

`tools/precedent_bootstrap_source.py` writes all three `individual` fields
for you when it creates a set, and
`tools/precedent_source_bootstrap.py` keeps them current at session start.
Filling them in by hand is for a machine where neither has run — copy
[templates/practice-set-individual/config.json.sample](templates/practice-set-individual/config.json.sample),
which carries the same explanation.

## Setting These on the Environment, With an Example for Each

**Recommended, not required.** Precedent installs and runs with none of this
set. What it buys is that three problems stop recurring per session: private
practices that silently never load, commits authored by the assistant's bot
account instead of a person, and attached repositories nobody checks for
staleness. Set on the environment rather than per checkout, they follow a
session into every repository it touches.

| Variable | Status | Example value |
|---|---|---|
| `PRECEDENT_GIT_TOKEN` | Required to reach a private practice set from a hosted session; irrelevant without one | `github_pat_<the rest of your read-only token>` |
| `PRECEDENT_SOURCE_BASE_URL` | Required whenever `PRECEDENT_GIT_TOKEN` is set — the token says you may read, this says what to read | `https://github.com/your-github-account` |
| `PRECEDENT_COMMIT_NAME` | Recommended | `Your Name` |
| `PRECEDENT_COMMIT_EMAIL` | Recommended, alongside the name | `you@example.com` |
| `PRECEDENT_COMMIT_TZ` | Recommended, alongside the name — without it a fallback zone is used and commit timestamps carry the wrong offset | `America/Argentina/Buenos_Aires` |
| `PRECEDENT_FRESHNESS_ALSO` | Recommended if practice sources are cloned beside your project | `~/precedent-individual=main;~/precedent-team-writing=main` |
| `PRECEDENT_GIT_TOKEN_USER` | Optional; defaults to `x-access-token` | `x-access-token` |
| `PRECEDENT_INDIVIDUAL_REPO` | Optional; only if your individual set is under a different account than the team sets | `https://github.com/another-account/precedent-individual` |

**Give your environments distinct names, and set a throwaway
`PRECEDENT_PING=1` beside the token.** Verified 2026-09-08: an account can hold
two environments with the SAME NAME — the selector gives you no way to tell
them apart — and three sessions across two fresh containers reported
`env | grep -c PRECEDENT` as **0**, with not one user-defined variable of any
kind. That reads exactly like "the runner does not pass variables through",
and was not that: `list_environments` showed two environments both named
`Default`, created 100 ms apart, with the variables set on one and the sessions
running in the other. The ping separates "the variables do not arrive" from
"the token is wrong", which print identically otherwise. An environment change
never reaches a session already running, so test in a NEW one. Full sequence:
[record/GOTCHAS_ARCHIVE.md](record/GOTCHAS_ARCHIVE.md) entry 29.

## Hosted Sessions — The Credential That Replaces `add_repo`

**On a hosted, ephemeral session there is a second way to reach your
private sources, and it is the durable one.** The usual route is the agent
calling `add_repo` in its first turn; that grants access *per session*, and
it **refuses across owners** — reproduced 2026-09-09 as the very first tool
call of a session whose initial repository was `alex137/bestpractice`:
*"cross-tier adds are not supported in v1"*. There is no ordering of calls
that gets around it, because the initial repository already counts. A
session in that state runs on the universal catalogue alone and **says so
only on stderr**.

A credential the *environment* carries is under no such ordering. The
SessionStart hook runs before the agent's first turn, so with these two
variables set it clones the sources then, and `add_repo` never enters into
it.

| Setting | Where | Effect |
|---|---|---|
| `PRECEDENT_GIT_TOKEN` | the environment's own configuration (on Claude Code on the web, the environment; locally, your shell profile) | A token with **read** access to your practice-set repositories. [tools/precedent_source_bootstrap.py](tools/precedent_source_bootstrap.py) uses it to clone them at session start — and, since 2026-09-11, to fast-forward the ones already on disk, so a container that has been up for days is not still reading the sources as they were the day it started. A clone with uncommitted work in it is reported and left alone, never clobbered. Since 2026-09-11 each synced clone also keeps the credential helper in its own config, so a later plain `git fetch` inside it works too — the helper names the variable, so no token is written to disk. Nothing else reads it. |
| `PRECEDENT_SOURCE_BASE_URL` | same | Where a practice set is cloned from, by name: `<base>/<set-name>`, e.g. `https://github.com/<account>`. Covers the **individual** set as well as the team ones (since 2026-09-10) — [source-naming](practices/source-naming.md) fixes that set's name to `precedent-individual` for everybody, so the account is the only unknown and this supplies it. Without it neither can be located, since **no tracked file names the account that owns them** — that is deliberate, and [precedent.json](precedent.json)'s own comment says why. |
| `PRECEDENT_GIT_TOKEN_USER` | same | Optional. The username sent with the token; defaults to `x-access-token`, which GitHub accepts alongside any personal access token. |
| `PRECEDENT_INDIVIDUAL_REPO` | same | Optional. The individual set's full URL, overriding the `<base>/precedent-individual` derivation above. Needed only where that set does not sit under the same account as the team sets. |
| `PRECEDENT_GIT_TOKEN=inherit` | same | Opt-in: use whatever git credential the container itself carries (`GITHUB_TOKEN`, then `GH_TOKEN`). **Expect it to be refused** — see below. |

**About `inherit`, and why it is opt-in rather than a fallback.** A Claude
Code on the web container already carries a GitHub token, and it is scoped to
the repositories the session attached — so for a practice set under another
owner it does not work. **Measured 2026-09-09**: `inherit` against a real
cross-owner private set was refused by GitHub with *"Invalid username or
token"*. That is a useful answer rather than a wasted one, because the
clone's own diagnosis distinguishes a **refused** credential from an absent
one, so the failure names itself. What it must never be is automatic: a token
nobody chose to send, sent anyway, turns "you have not set a credential" into
"your credential is wrong", which is the more expensive of the two to chase.
Ask for it by name, or set a real token.

**Use a read-only token, scoped to the practice-set repositories.** Nothing
here pushes with it.

**A practice set is a repository you work in, and since 2026-09-13 it gets
the same hook a consuming repo does.** Before that, a session rooted in
`precedent-individual` or any `precedent-team-*` resolved **no individual
practice source at all** — nothing there ever wrote
`~/.config/precedent/config.json` — so every personal rule was silently
absent while the session applied the ones it could see. The hook that writes
it now ships into a set as well
([tools/precedent_bootstrap_source.py](tools/precedent_bootstrap_source.py)),
execing the same vendored
[tools/precedent_source_bootstrap.py](tools/precedent_source_bootstrap.py),
which a set may hold for the first time. **A set created before that date
has neither the hook nor the wiring**, and this cannot be repaired for you:
an existing `.claude/settings.json` is never rewritten, so
[tools/precedent_refresh_sources.py](tools/precedent_refresh_sources.py)
reports the hook as unwired at every session start. The hook file and the one
`SessionStart` command are both yours to add there — `--apply` writes neither
for a set whose settings do not already declare the hook — ahead of
`commit-identity.sh`, which reads that set for the author and the timezone.

**Verified end to end, 2026-09-10.** A real read-scoped token set on the
environment, and a brand-new container came up with all four private sources
already cloned, before the first turn:
[tools/precedent_resolve.py](tools/precedent_resolve.py) reported **146
practices from 6 sources (41 team, 13 individual)** in a repository that had
been resolving 89 from 1, and
[tools/precedent_source_credentials.py](tools/precedent_source_credentials.py)
reported `OK`. No `add_repo` call was made or needed. **What made this look impossible
for three days was not the token**: the account held two environments with
the same name, and the values had been set on the one the sessions were not
running in. Name your environments distinctly — see [AGENTS.md](AGENTS.md)'s
gotcha and, for the full sequence, entry 29 in
[record/GOTCHAS_ARCHIVE.md](record/GOTCHAS_ARCHIVE.md).

**What was verified before that, and how (measured 2026-09-09, in a Claude
Code on the web container).** Three things were tested directly: an
authenticated request to `github.com` **leaves the sandbox and reaches
GitHub's own authentication** rather than being stopped by the proxy; there
is **no ambient credential** for a private repository, so nothing works by
accident; and the credential helper this ships **does deliver** the token to
git — with a deliberately invalid one, git did not fall back to prompting,
it sent the credential and GitHub rejected it. A valid token stayed untested until 2026-09-10,
when it worked on the first try — recorded above.

**The token is never written down.** It reaches git through a helper that
reads the environment variable itself, so it appears in no command line, no
clone's `.git/config`, and none of the files the bootstrap writes.

**Setting the variable does not reach a session that is already running**,
and the check below reads identically for "never set" and "set five minutes
ago" — which is exactly how a correct configuration gets reported as a broken
one (2026-09-09: a resumed session in a container that predated the change
measured **zero** `PRECEDENT_*` variables, not an empty token). **Test an
environment change in a NEW session**, and run `env | grep -c PRECEDENT`
before concluding anything about the token itself.

**If the token is not set, there are two fallbacks and then nothing.** In
order:

1. **`add_repo` from inside the session**, which grants access for that
   session only. It works when the practice sets and the repository you are
   working in belong to the **same GitHub owner**; across owners it refuses,
   and no ordering of calls avoids that — the initial repository already
   counts.
2. **Start the session rooted at the practice set itself**, and reach the
   other repository by a plain `git clone` if it is public. This is what the
   cross-owner case is left with, and it is why work spanning both owners
   gets split across two sessions.
3. **Nothing else, by design.** There is no offline copy to fall back on: a
   private set's text may not be vendored into a repository other people can
   read, which is the whole reason it is a separate private repository. So
   when neither route is available, **the session runs on the universal
   catalogue alone** — and the only protection left is knowing it. That is
   what every line below is for; a session in this state should say so in its
   reply rather than let the reader assume the personal and team rules were
   applied.

**Check it from inside any session:**

```
python3 tools/precedent_source_credentials.py
```

It reports `OK` when every private source this repository expects is on
disk, `MISSING` when one is absent and no credential is set — the state
worth acting on — and `SET` when one is absent *despite* a credential,
which means the token is not the problem and the clone itself is. The same
line is printed by the session check, by the source-freshness report at
session start, and by a vendor update.

A fourth verdict, **`UNCONFIGURED`**, says the one thing the other three
cannot: the only source missing is your **individual** set, and the reason
is the user-level config rather than anything a credential reaches — the
file is absent, or will not parse, or parses and names no individual
source. Those are three different states with three different remedies, and
none of them is a token. It exits 0, because nothing is in the wrong state;
on a hosted session an absent or empty config still reads as `MISSING` or
`SET`, since the bootstrap writes that file only after a clone succeeds, so
a clone that failed leaves exactly the same fingerprint.

## Optional, and Each One an Escape Hatch

| Setting | Where | Effect |
|---|---|---|
| `git config precedent.freshness.intervalSeconds` | per checkout | How long the freshness guard's `user-prompt` mode stays quiet between checks. Default 600. |
| `git config precedent.freshness.override true` | per checkout | Stops the guard refusing a write on a stale checkout. Deliberate override; the guard prints this remedy itself when it blocks. |
| `PRECEDENT_FRESHNESS_ALSO` | environment | `;`-separated `<path>=<base branch>` entries naming repositories the session merely has **attached** — a sibling clone a team source resolves to, anything `add_repo` handed it. A hook only ever fires for the project dir, so without this an attached repo runs none of its own freshness checking, however correctly its guard is installed. Unset, nothing changes. An entry naming a path that is absent or is not a git repository is reported and skipped, never blocked on. Set it on the environment, like `PRECEDENT_COMMIT_*` below and for the same reason: environment variables follow a session into every repository it touches. **Write a path under your home directory as `~/name` or `$HOME/name`, not spelled out**: an individual practice source lives at `$HOME/precedent-individual`, and `$HOME` is not the same on every container, so an absolute path written on one names nothing on the next — silently, since a dead entry is skipped rather than blocked on. `$CLAUDE_PROJECT_DIR` is expanded too. `python3 tools/precedent_session_check.py` reports any entry that resolves to nothing and prints the value to set instead. |
| `PRECEDENT_INDIVIDUAL_REPO` | environment | Overrides `individual.repo_url` for one session — for an environment that sets per-session variables and would rather not touch the config file. |
| `PRECEDENT_COMMIT_NAME` / `_EMAIL` / `_TZ` | environment | The commit-identity layer that reaches a repository attached mid-session, which no hook can. Normally derived from your individual set's `identity.json` by the harness adapter's `env` block rather than set by hand. |
| `PRECEDENT_ALLOW_ANY_AUTHOR=1` | one command | Lets a single commit through the author check. For a commit deliberately authored by someone else. |
| `PRECEDENT_USER_CONFIG` | environment | Points at a user config somewhere other than the default path. Useful for testing an empty-neighbourhood case without disturbing your own. |

`PRECEDENT_CHECK_ROOT` and `PRECEDENT_VENDOR_ENGINE_SECOND_PASS` are
deliberately omitted: both are internal to a check or a tool's own test
harness, and neither is a person's setting.

