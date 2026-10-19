# Shared sets copied into a repository

A shared set can be copied into the repository that uses it, the way the
universal catalogue already is at `process/upstream/`. Update Vendors
refreshes the copy, a guard refuses hand edits to it, and nothing has to
attach or clone it when a session starts, so it cannot fail to arrive.

This is the engine half of a plan written in a private repository on
2026-10-19, after attached sets kept failing to load at session start (the
gotchas from 2026-09-06, 2026-09-08, 2026-09-11, 2026-09-07 and 2026-09-25
each record one way). The plan also covers which sets one person copies
into which of their repositories; those parts name private repositories
and stay there.

## How a repository says it

A source entry in `precedent.json` carries `"vendored": true` and points
`path` inside the repository:

```json
{"level": "shared", "name": "precedent-shared-ladder",
 "path": "process/precedent-shared-ladder", "vendored": true}
```

Nothing changes in a repository that does not say this.

## What each part of the engine does with it

| Part | What it does | Where |
|---|---|---|
| The resolver | Loads the copy from `path` like any declared set. A set a person brings with the same name is left out: the repository's copy wins, so everyone in the repository runs the same version. | `load_config` and `is_vendored` in [tools/precedent_resolve.py](../tools/precedent_resolve.py) |
| The list of clones | `declared_source_paths` leaves a copy out, because it is part of this checkout and nothing may fetch it, ask git for its branch or test it as a clone. `vendored_source_paths` lists the copies for the callers that want every set on disk. | [tools/precedent_resolve.py](../tools/precedent_resolve.py) |
| Update Vendors' copy | `checkin.py --source <name>` mirrors the set's `practices/` and `precedent-source.json` (and its `code` directories, if any), and records the commit it took, where the copy lives (`vendored_at`) and where it came from (`repo`) in `process/manifest_<name>.json`. | [tools/checkin.py](../tools/checkin.py) |
| The hand-edit guard | The same byte-identical check `process/upstream/` has. A change to a rule is made in the set's own repository, then taken by Update Vendors. | `copy_drift` in [tools/checkin.py](../tools/checkin.py), run by the `vendored-copy-matches-record` check |
| Freshness | A copy whose origin has moved is reported `BEHIND UPSTREAM`, like the universal catalogue. | [tools/precedent_engine_freshness.py](../tools/precedent_engine_freshness.py) |
| Private sets | A private set is copied only into a repository whose `precedent.json` says `"visibility": "private"`. Update Vendors refuses the copy otherwise, and the `copied-in-set-fits-visibility` check refuses one made another way. A public set's copy is not mistaken for a leak by its folder name. | `_refuse_private_into_public` in [tools/checkin.py](../tools/checkin.py); [tools/precedent_check.py](../tools/precedent_check.py); `private_set_names` in [tools/leak_gate.py](../tools/leak_gate.py) |
| Session start | Does not fetch a set the repository copies in, and does not count it as missing from what the person brings. A copy that is not there is reported as Update Vendors' to make, never as a set to attach. | [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py), [tools/precedent_session_check.py](../tools/precedent_session_check.py), [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py) |

The test is `check_copied_in_shared_sets` in
[tools/verify_harness.py](../tools/verify_harness.py), with the guard's
negative control (a rule edited in the copy is found).

## Still to build

- **The ladder, bound by one code owner.** The `ladder-set-is-brought-not-declared`
  check refuses a repository that declares the ladder (decision D18 of
  [LADDER_OPT_IN_PLAN.md](LADDER_OPT_IN_PLAN.md)). It is narrowed, not
  dropped: one code owner's quoted yes in a `binds_everyone` entry lets a
  repository declare it.
- **A set carried inside another.** A copied set may carry a second set
  inside it; the repository's own declaration of that second set wins.
- **The question, asked once.** Installing Precedent, and the one Update
  Vendors that brings this into an existing repository, ask the person
  whether to copy in each set they bring, and record the answer, yes or
  no, in `precedent.json`.

## Rolling back

In one repository: point the source back at a sibling clone, drop
`"vendored"`, delete `process/<name>/` and its manifest, and run the sync.
No other repository is touched.
