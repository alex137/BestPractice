<!-- Last updated: 2026-09-05 (Buenos Aires) by the session that closed the source-repo vendored-engine gap this document names, and again the same day by the session that closed its consumer-repo sibling gap (see "The four-source CONSUMER case" below) -->

# Bootstrapping a Brand-New Individual or Team Set

This is the generalized, repeatable procedure for the case
[the guided-install conversation](../SETUP.md) step 2 and
[INSTALL.md](../INSTALL.md) step 9 both used to leave as a dead end: an
adopter with **no** individual practice repo and **no** team practice repo
yet, who wants one. It exists because every other piece of documentation
about individual/team sources — this document included until now —
assumed the repo already existed.

**This is a different document from
[PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md), on purpose.** That brief
records how `themorgan/precedent-individual` and
`themorgan/precedent-team-maintainers` were actually populated: bespoke,
one-off work, done from a session opened directly against those two
already-*existing* private repos, carrying RepoPersonalPreferences' (RPP)
real 46 rules across.
It is a historical record of this project's own phase-3 work, not a
procedure anyone else should follow. This document is the opposite: no
private content, no existing repo assumed, meant to be followed by any
adopter, any number of times.

## What the tool does, and does not do

[`tools/precedent_bootstrap_source.py`](../tools/precedent_bootstrap_source.py)
mechanizes everything that does not require credentials this tool can't
assume a session has:

- Copies [`templates/practice-set-individual/`](../templates/practice-set-individual/)
  or [`templates/practice-set-team/`](../templates/practice-set-team/) into
  a target directory, filling in the owner's name (and, for a team, its
  first approver's name and GitHub handle) wherever the skeleton names a
  placeholder.
- **Vendors a real engine into the new set's own `tools/`** —
  [`tools/precedent_vendor_engine.py`](../tools/precedent_vendor_engine.py)'s
  `seed()`, called from `bootstrap()` itself, with no separate step to
  remember. This is no longer optional or manual: every set this tool
  produces gets `build_views.py`, `precedent_gate.py`, `precedent_paths.py`,
  `precedent_show.py`, `split_practices.py`, a trimmed `routing_scope.json`,
  and `precedent_vendor_engine.py` itself (so the vendoring mechanism can
  update its own already-bootstrapped copies too), plus a
  `tools/ENGINE_MANIFEST.json` recording which BestPractice commit it came
  from and a sha256 per file. See "The vendored engine" below — this is new
  as of this document's 2026-09-05 update; before it, the tool wrote only
  practice content, config, approvers and the leak-blocklist, and every
  engine copy that existed (`precedent-individual`,
  `precedent-team-maintainers`) came from an undocumented, one-off
  hand-copy that nothing could tell was stale (`precedent-team-tms`'s was
  simply missing).
- Refuses to write into a non-empty destination without `--force true`.
- Prints — or, opted in with `--write-user-config true` /
  `--write-repo-config PATH`, writes — the exact wiring the next step
  needs: the `~/.config/precedent/config.json` `individual` block, or the
  consuming project's `precedent.json` `"sources"` entry.

**It never touches a git remote or any hosting API.** Creating the actual
repository — `gh repo create`, or a few clicks on GitHub — needs
credentials or a platform capability this tool can't assume any given
session has, and guessing wrong there is worse than asking. That step
stays explicit, below.

## The vendored engine

A brand-new individual or team set is a source repo, not a four-source
consumer — it has no `process/upstream/` tree and no use for
[`precedent_materialize.py`](../tools/precedent_materialize.py)/
[`precedent_resolve.py`](../tools/precedent_resolve.py)/
[`precedent_sync_views.py`](../tools/precedent_sync_views.py), which only
a consumer resolving universal+team+individual+repo-local sources together
needs. What it needs is just enough to run its own
`AGENTS.md` loader block: the five files
[`tools/precedent_vendor_engine.py`](../tools/precedent_vendor_engine.py)'s
own docstring names as `ENGINE_FILES`, plus a routing-vocabulary fixture
(`routing_scope.json`, trimmed to the closed gate vocabulary
[`precedent_gate.py`](../tools/precedent_gate.py) needs — BestPractice's
own copy also documents the routing reason for every one of *its* 60-odd
practices, which has no meaning in a different catalogue).

`precedent_vendor_engine.py` is itself one of the vendored files, on
purpose: it travels with the engine it defines, so an improvement to the
vendoring mechanism reaches an already-bootstrapped set the same way an
improvement to [`build_views.py`](../tools/build_views.py) does. Once a
set exists, refreshing it later needs a sibling clone of BestPractice (the
same shape [`tools/checkin.py`](../tools/checkin.py) already uses for a
consumer's check-in cycle) and one command:

```
python3 tools/precedent_vendor_engine.py status  ../BestPractice   # drift? behind?
python3 tools/precedent_vendor_engine.py refresh ../BestPractice   # pull, re-vendor, re-stamp
```

### How a set finds out it is behind

Until 2026-09-06 there were none, and the cost was real: two live sets sat
more than two hundred commits behind this repo, both generating a loader
block with a defect fixed upstream days earlier. Nothing was broken — there
was simply no channel through which *"your copy is behind"* could reach
anyone. It surfaced only because a session happened to have a clone of this
repo attached and happened to run `status` by hand.

The reason a source set was harder than a consumer repo is worth stating,
because it explains the shape of all three answers. A consumer vendors
`process/upstream/` and its bootstrap runs a freshness check at session
start. A source set could not do the same: `refresh` needs a clone of *this*
repo to compare against, and a person's ordinary session has no reason to
have one.

| Channel | Runs | Needs a clone? |
|---|---|---|
| The warning [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py) prints when the checkout it is seeding *from* is itself behind | At bootstrap | No — it is running inside one |
| [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py), from a session working in this repo | Every session start here | No — this checkout *is* the clone |

Both are incidental: they fire when someone happens to be bootstrapping, or
happens to be working in this repo. Neither runs on a schedule, so a set
nobody touches for a month is told nothing for a month.

### The scheduled channel, and why it is not shipped here

The obvious third channel is a weekly GitHub Actions job in the source set
itself: clone this repo, refresh, regenerate, open a pull request. It works,
and it is the only channel that fires whether or not anyone is looking.

**It was added to both source templates on 2026-09-06 and removed the same
day.** Not because it broke — because a template is the wrong place to make
that choice. A scheduled workflow inherited by every adopter is a cron job
phoning a remote every week, consuming their Actions minutes, opening pull
requests in their repository, on a schedule they did not pick. That is a
real imposition, and "it is good for you" is not a reason to install it in
someone's repo without asking. It now lives at the **individual level**, in
the practice set of whoever wants it, which is where a preference about how
one's own repositories behave belongs
([`layered-practice-packs`](../practices/layered-practice-packs.md)).

Anyone who wants it can build it — the shape, recorded here so it does not
have to be re-derived:

- Clone this repo's `precedent-beta-v01`, run `precedent_vendor_engine.py
  refresh`, then `build_views.py`. **Both**, in one commit: a refreshed
  generator whose views have not been re-run leaves the set failing its own
  `build_views --check`.
- Use the resulting **diff** as the signal — `git status --porcelain` empty
  means the engine was already current. Do not parse a notice string.
- Push a branch, then try to open a pull request. This needs a GitHub
  setting that is **off by default** and that an organization or enterprise
  can withhold entirely: *Allow GitHub Actions to create and approve pull
  requests*, under Settings → Actions → General → Workflow permissions.
- **Do not let the notification depend on that setting.** Fall back to
  opening an issue, which needs only `issues: write` and which nothing
  gates; put a `compare/<base>...<branch>?expand=1` link in it so the person
  opens the pull request themselves in one click. Fall back *only* on that
  specific permission error, so an unrelated failure still fails loudly.
- Keep one issue, reused, and close it when a later run finds the engine
  current — so an open issue means *stale now*, not *was stale once*.

```
```

`refresh` pulls BestPractice's `precedent-beta-v01` branch specifically —
not whatever branch is configured as the clone's default — because that is
where routine engine work lands until Alex's own, deliberate phase-7
fold-in into `main` (see
[`local/practices/merge-target-is-beta-branch.md`](../local/practices/merge-target-is-beta-branch.md)).
It refuses to overwrite a vendored file that was hand-edited locally
(detected by comparing the file's sha256 against what `ENGINE_MANIFEST.json`
recorded) unless `--force` is passed — this engine is meant to carry zero
local variance, so a hand-edit is a signal something needs to move
upstream into BestPractice instead, not to be silently discarded.

**Why this isn't `tools/checkin.py` extended, rather than a new tool**:
`checkin.py` mirrors a consumer's entire `process/upstream/` tree,
deleting anything the tree no longer has, in both directions. A source
repo's `tools/` directory holds vendored engine files *alongside*
non-vendored, repo-owned ones (`tools/checks/`, most obviously) that a
whole-directory mirror-and-delete would destroy, and the flow here is
one-directional (a source has nothing of its own to check in upstream) —
different enough on both axes that overloading `checkin.py` with a second
manifest shape and a "named file set" mode would have cost more clarity
than a small, purpose-built tool.

**The four-source CONSUMER case, closed 2026-09-05.** This document and
`precedent_vendor_engine.py`'s `'source'` kind closed the gap above for a
*source* repo (an individual or team set) first. A real four-source
consumer (universal + team + individual + repo-local, with
`process/upstream/` and the full `precedent_materialize.py`/
`precedent_resolve.py`/`precedent_sync_views.py` toolchain) needed the same
treatment — TODO.md tracked it as open, named explicitly so "the
source-repo case is solid" was not mistaken for "the consumer case is
solid too." It no longer is: `precedent_vendor_engine.py`'s `'consumer'`
kind (same script, same seed/status/refresh/fresh subcommands, a larger
CONSUMER_ENGINE_FILES list) closes it, piloted against the real
`themorgan/HavrutaBrainstorm` repo. See
[`INSTALL.md`](../INSTALL.md)'s §0 step 1 and its "Keep the vendored engine
current (consumer repos)" step under §2 for the consumer-repo procedure,
and `tools/verify_harness.py`'s `check_vendor_engine_consumer_case()` for
the fixture proving the whole four-source pipeline actually runs through a
consumer's own vendored copy, the same rigor
`check_bootstrap_source_engine_is_functional()` applies to the source-set
case documented above.

## The procedure

### For an individual set

1. **The name is not a choice: an individual set is always called
   `precedent-individual`**, in that person's own account, which already
   namespaces it. Say so before the person creates anything — the naming
   convention is [practices/source-naming.md](../practices/source-naming.md),
   the reasoning is in [spec/SOURCE_NAMING.md](SOURCE_NAMING.md), and
   [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
   refuses any other `--name` before it creates anything, and
   [tools/precedent_resolve.py](../tools/precedent_resolve.py) refuses a
   source declared under one.
2. Create a **private** repository under the person's own account. If the
   session has the access to do this itself (a GitHub App/token scoped for
   repo creation), do it directly; otherwise hand the person the exact
   command (`gh repo create <name> --private`) or the exact click-path
   (github.com → **New repository** → private → no template).
3. Run:
   ```
   python3 tools/precedent_bootstrap_source.py --level individual \
       --name <name> --dest <local clone path>
   ```
4. `cd` into the destination, `git init` (if step 2's repo creation didn't
   already leave a clone), commit everything, add the remote from step 2,
   push.
5. Either pass `--write-user-config true` on the bootstrap command (step 3)
   to write `~/.config/precedent/config.json` directly, or copy the printed
   snippet there by hand. **Never** write this into any shared project's
   own tracked files — see `precedent_resolve.py`'s own header for why
   that's refused outright, not just discouraged. On a machine where
   `$HOME` doesn't persist between sessions (Claude Code Remote/Web), skip
   straight to step 5b below instead — a config written by hand here would
   just be gone next session.
5b. **On a hosted/ephemeral session, also wire the session-start hook** —
   `--write-session-hook <consuming project path> --repo-url <this set's
   real git remote, from step 4>` on the same bootstrap command — or, for a
   set that already exists, run it with **no `--dest`** and those two flags
   plus `--level individual --name`, which writes the hook and creates or
   touches nothing else. (That second form only became possible on
   2026-09-06: `--dest` was required either way, so "run it again against an
   already-bootstrapped set" meant force-overwriting the set to get a hook,
   and BestPractice itself therefore had none.) This instantiates
   [`templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template`](../templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template)
   into the *consuming* project's `.claude/hooks/precedent-individual-bootstrap.sh`,
   delegating to
   [`tools/precedent_source_bootstrap.py`](../tools/precedent_source_bootstrap.py) —
   see that file's own module docstring, and
   [`practices/session-bootstrap.md`](../practices/session-bootstrap.md)'s
   Story, for why this hook's own attempt, by itself, structurally cannot
   succeed on a fresh session: its repo-read access is granted by the
   agent's own `add_repo` call, made in the agent's own turn, and a
   `SessionStart` hook runs *entirely to completion* before that turn
   starts — not a race the hook might win with enough tries, an ordering
   it cannot win even once. So the consuming project's instructions file
   still needs the standing `add_repo`-at-session-start instruction
   ([INSTALL.md step 9](../INSTALL.md#1-install-into-a-dependent-repo),
   [spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)
   step 4) alongside this hook — what actually saves the session is
   `tools/precedent_resolve.py`'s own lazy self-heal re-invoking this same
   hook later, from inside the agent's own turn, after that instruction has
   already run.
5c. **If the project already carries someone else's hook, do not add a
   second one — set `PRECEDENT_INDIVIDUAL_REPO` to your own set's URL.**
   The hook is committed to a *shared* project, but an individual set
   belongs to one person, so the account baked in when it was instantiated
   is right for whoever installed it and wrong for every other person on
   that project. The instantiated hook reads `PRECEDENT_INDIVIDUAL_REPO`
   first and falls back to the baked-in default, so each person points it
   at their own account through their environment — on Claude Code Remote,
   the environment's own variable configuration — while the tracked file
   stays one file with one default. The *name* is deliberately not
   overridable: [practices/source-naming.md](../practices/source-naming.md)
   fixes it as the same string in every person's own account, so only the
   account can legitimately differ. (Added 2026-09-06, when this repo
   installed its own hook and baked in the one individual set that exists
   here — correct for its owner, wrong for the second maintainer, and
   nothing was going to say so.)
6. Fill in `leak-blocklist.txt` with the person's own private terms, then
   `export PRECEDENT_LEAK_BLOCKLIST=<path>` and
   `git config precedent.requireVocabulary true` in every shared project
   they work in.
7. Delete `practices/example-starter.md` once a real first practice
   replaces it.

### For a team set

Same shape, with two differences: the repo is created once per team (not
per person), and it needs at least one approver at creation time.

1. **The name is `precedent-team-<slug>`**, slug lowercase and hyphenated,
   naming what the team is *for* rather than who is on it — a roster-shaped
   name is stale the moment a third person joins, and renaming a set breaks
   every vendored reference to it. Say the convention before the repository
   is created; see [practices/source-naming.md](../practices/source-naming.md).
2. Create a **private** repository, shared with the team's members as
   collaborators. Same access caveat as step 2 above.
3. Run:
   ```
   python3 tools/precedent_bootstrap_source.py --level team \
       --name <name> --dest <local clone path> \
       --approver "Full Name:github-handle"
   ```
   (Comma-separate multiple `name:handle` pairs to seed more than one
   approver at creation — still fine per
   [PRACTICE_ENGINE_PLAN.md's Stage 4](../PRACTICE_ENGINE_PLAN.md#stage-4--approval-by-level):
   "whoever creates a team set is its first approver. No ceremony.")
4. `cd` into the destination, `git init`/commit/push, same as the
   individual case.
5. Wire it into the **consuming project's own tracked `precedent.json`**
   (this one *is* meant to be shared — everyone on the project reads it):
   either pass `--write-repo-config <project root>` on the bootstrap
   command, or add the printed `"sources"` entry by hand, per
   [INSTALL.md step 9](../INSTALL.md#1-install-into-a-dependent-repo).
6. On a hosted/ephemeral session where nothing under the project's git
   checkout persists between sessions, wire the sibling-checkout access
   the same way [spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)'s
   step 4 already documents for an existing team source — this is the
   identical gap, not a new one.
7. Fill in `leak-blocklist.txt` and `approvers.json` for real, delete
   `practices/example-starter.md` once a real first practice replaces it.
8. **For a team set, run `python3 tools/build_codeowners.py`** and commit
   the `CODEOWNERS` it writes. `approvers.json` is the declaration;
   `CODEOWNERS` is what actually makes GitHub require an approver's review,
   and until it exists the approver list enforces nothing. Re-run it every
   time `approvers.json` changes; never hand-edit the generated file. (An
   individual set skips this — it has no `approvers.json`, and one person
   is the whole approval mechanism. The tool says so and exits 0 rather
   than failing, so running it there is harmless.)

## What this does not close

- **Repo creation itself stays a human/session step**, per the "what the
  tool does not do" section above — this document does not pretend
  otherwise.
- **This is not [`spec/PHASE6_BRIEF.md`](PHASE6_BRIEF.md) item 2** (wiring
  the full candidate/proposal pipeline — `precedent_candidate.py`,
  `precedent_promote.py`, `precedent_land.py` — into a consuming repo).
  That item is about *proposing new practices upward* once a set already
  exists; this document is about the set existing in the first place. A
  freshly bootstrapped set works today with direct edits (as
  `examples/practice-set/` already shows) — the creation-pipeline tooling
  is a separate, still-open piece of work.
- **Not rehearsed against a real, brand-new external adopter yet** — the
  harness checks (`check_bootstrap_source_produces_resolvable_set` proves
  the tool's *content* output resolves cleanly against a synthetic consumer
  repo; `check_bootstrap_source_engine_is_functional` proves the *engine*
  half is real and working, not just present — both in
  `tools/verify_harness.py`) prove the tool's output is sound; neither
  proves the full human-in-the-loop procedure above reads well to someone
  who has never seen Precedent before. Worth a real rehearsal the same way
  [spec/PHASE6_BRIEF.md](PHASE6_BRIEF.md) item 4 flags for the loader
  install path generally.
