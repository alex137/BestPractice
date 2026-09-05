<!-- Last updated: 2026-09-05 (Buenos Aires) by the session that closed the vendored-engine gap this document names below -->

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
non-vendored, repo-owned ones (`tools/checks/`, and
`precedent-team-maintainers`' own `build_codeowners.py`) that a
whole-directory mirror-and-delete would destroy, and the flow here is
one-directional (a source has nothing of its own to check in upstream) —
different enough on both axes that overloading `checkin.py` with a second
manifest shape and a "named file set" mode would have cost more clarity
than a small, purpose-built tool.

**Not yet built: the four-source CONSUMER case.** This closes the gap for
a *source* repo (an individual or team set). A real four-source consumer
(universal + team + individual + repo-local, with `process/upstream/` and
the full `precedent_materialize.py`/`precedent_resolve.py`/
`precedent_sync_views.py` toolchain) has not been piloted with a vendored,
refreshable engine of its own — [`INSTALL.md`](../INSTALL.md) already
documents that install path, but extending it to vendor the engine the
same disciplined way is separate, real, still-open follow-up work. Do not
read "the source-repo case is solid" as "the consumer case is solid too."

## The procedure

### For an individual set

1. Pick a name (by convention, `<your-name>-individual` or similar — see
   [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md#what-morgan-needs-to-do)'s
   naming convention for the pattern this project itself used).
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
   real git remote, from step 4>` on the same bootstrap command (or run it
   again against an already-bootstrapped set). This instantiates
   [`templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template`](../templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template)
   into the *consuming* project's `.claude/hooks/precedent-individual-bootstrap.sh`,
   delegating to the retry-capable
   [`tools/precedent_source_bootstrap.py`](../tools/precedent_source_bootstrap.py) —
   see that file's own module docstring, and
   [`practices/session-bootstrap.md`](../practices/session-bootstrap.md)'s
   Story, for why a single-shot clone attempt here isn't enough: this
   hook's own repo-read access is granted by the agent's own `add_repo`
   call, made in the agent's own turn, and a `SessionStart` hook runs
   *before* that turn starts — so the consuming project's instructions file
   still needs the standing `add_repo`-at-session-start instruction
   ([INSTALL.md step 9](../INSTALL.md#9-ask-about-team-and-individual-practice-sources),
   [spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)
   step 4) alongside this hook, not instead of it.
6. Fill in `leak-blocklist.txt` with the person's own private terms, then
   `export PRECEDENT_LEAK_BLOCKLIST=<path>` and
   `git config precedent.requireVocabulary true` in every shared project
   they work in.
7. Delete `practices/example-starter.md` once a real first practice
   replaces it.

### For a team set

Same shape, with two differences: the repo is created once per team (not
per person), and it needs at least one approver at creation time.

1. Pick a name (by convention, `<team-name>-maintainers` or similar).
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
   [INSTALL.md step 9](../INSTALL.md#9-ask-about-team-and-individual-practice-sources).
6. On a hosted/ephemeral session where nothing under the project's git
   checkout persists between sessions, wire the sibling-checkout access
   the same way [spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)'s
   step 4 already documents for an existing team source — this is the
   identical gap, not a new one.
7. Fill in `leak-blocklist.txt` and `approvers.json` for real, delete
   `practices/example-starter.md` once a real first practice replaces it.

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
