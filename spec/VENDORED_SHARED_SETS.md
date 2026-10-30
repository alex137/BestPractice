---
title:         Shared sets copied into a repository
kind:          reference
status:        current
opened:        2026-10-19
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "A shared set can be copied into the repository that uses it, like the universal catalogue at process/upstream/: Update Vendors refreshes the copy, a guard refuses hand edits, freshness reports it, a private set goes only into a private repository, and session start never has to attach it."
---

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

## A set that lives in a folder of its repository

Some sets share their repository with other things. A voice pack lives in
a repository that also runs its own Precedent install, so that
repository's `practices/` is its own rules, not the pack's. Such a set
keeps its `precedent-source.json`, `practices/` and anything it carries in
one folder, and the source entry that copies it in names that folder:

```json
{"level": "shared", "name": "<set>", "path": "process/<set>",
 "vendored": true, "set_root": "<folder>"}
```

Update Vendors' copy then takes that folder alone, and the copy reads as
the set itself. A `set_root` that leaves the repository is refused. A set
a person only offers names its folder in the same way (`offers` entries
take a `set_root`), and a yes to the question below writes it into the
source entry.

## Files a source exports

A source can export files for others to copy besides its rules: a voice
repository's compiled prompts, a rules file a tool reads. Its
`precedent-source.json` lists them, each a file or a folder inside the set
(under its `set_root`, when it has one):

```json
{"name": "<source>", "level": "shared",
 "exports": ["UNIFIED_VOICE_PROMPT.md", "essentials"]}
```

Every copy of the source brings them, beside its practices. A repository
that wants the files alone, and none of the source's rules in force,
declares the copy `exports_only`:

```json
{"level": "shared", "name": "<source>", "path": "process/<source>",
 "vendored": true, "exports_only": true}
```

That copy holds the exported files and the source's `precedent-source.json`,
nothing else; nothing loads rules from it. A source with no
`precedent-source.json` of its own is copied by naming the files in the
entry instead, `"exports": ["RULES.md"]`, which also narrows what a source
that does declare exports is taken for. The copy lands at `path`, which is
always `process/<source>`; whatever reads the files reads them there.

It is one mechanism (Morgan, 2026-10-30, strength: decided): the same
`checkin.py --source` copy and record, the same hand-edit guard, freshness
row, `hold` and `--take-set`. Update Vendors starts the record for a source
declared by hand, lists each file a refresh changed, and leaves for the
person any declared copy it could not refresh -- no clone on the machine,
or the copy failed -- rather than reporting DONE. A private source's
exports are copied only into a private repository, as its rules are.

**A copy nothing declares fails the full check.** The
`copied-in-folder-is-declared` check finds a folder copied in another way
by its signs -- a `.source-commit` or `.source-blob` file, or a file whose
first lines open with an `AUTO-SYNCED` or "vendored from" banner -- and
fails unless `precedent.json` declares a copied-in source there. A new copy
between repositories is added only as a declared source, and the script that
made the old one is retired.

The test is `check_declared_exports_are_copied` in
[tools/verify_harness.py](../tools/verify_harness.py), with a passing
control for each refusal.

## The ladder, bound by one code owner

The `ladder-set-is-brought-not-declared` check refuses a repository that
declares the ladder (decision D18 of
[LADDER_OPT_IN_PLAN.md](LADDER_OPT_IN_PLAN.md)), because a declared set
binds everyone there. It is narrowed, not dropped: a `binds_everyone`
entry in the repository's own `precedent.json` lets it declare the ladder
when one code owner says so.

```json
"binds_everyone": {
  "sets": ["precedent-shared-ladder"],
  "approved_by": "Name, 2026-10-19: \"their words\""
}
```

The name before the first comma must be one of the repository's code
owners: a login `precedent_audience.owners()` reads (CODEOWNERS, else the
registry it is generated from, else the repository's GitHub owner), or the
`name` that `maintainers` gives such a login. The entry needs a date and a
quote. One code owner is enough; in a repository with several, any one of
them can bind the rest without asking them, and the quote shows who did.
The test is in `check_ladder_test_session_and_the_two_ladder_checks`.

## A set carried inside another

A copied set may carry a second set inside it: a voice pack, say, carries
the writing rules it is built on, so a repository that copies the pack in
gets both and declares one. The carrier's `precedent-source.json` names
each carried set and where it sits, relative to the carrier:

```json
"carries": [{"name": "<set>", "path": "<folder inside this set>"}]
```

- **Update Vendors' copy brings it along**, whole, with its carrier.
- **The resolver puts it in force** at its place in the copy, unless the
  repository declares a set of that name itself: then the repository's
  own declaration wins, and only one copy is in force. A person who
  brings the same set gets the carried copy. (`carried_sources` and
  `carried_in_force` in
  [tools/precedent_resolve.py](../tools/precedent_resolve.py).)
- **Freshness:** the carried set moves with its carrier, so the carrier's
  row says whether it is behind; a note names the carried set, and says
  when it is not in force because the repository declares its own.
- **Private sets:** Update Vendors refuses a carrier that carries a private
  set into a repository not declared private, and the
  `copied-in-set-fits-visibility` check covers carried sets too.
- A `carries` path that leaves the set is ignored.

The test is `check_copied_set_carries_another` in
[tools/verify_harness.py](../tools/verify_harness.py).

## The question, asked once

Whether a repository copies a set in is a question put to the person at
two moments, and only those: installing Precedent into a new repository,
and the one Update Vendors that brings this system into an existing one.
The answer, yes or no, is recorded in that repository's `precedent.json`
and never asked again there (Morgan, 2026-10-19, strength: decided).

- **What is offered:** every set the person's individual set brings, and
  every set it only offers (its `precedent-source.json`'s `offers`, a list
  of `{name, repo_url}`: a voice pack, which nobody brings everywhere).
- **The default suggested:** "yes" for a set the person brings, only when
  the repository is private and its code owners are that person alone.
  "No" everywhere else, and always for a set they only offer. The
  person's answer always wins; nothing is copied in unanswered.
- **What the question says** (Morgan, 2026-10-19, after first meeting it
  in his practice sets): in a repository that is not private it opens
  with a warning that the repository is public, so the set's rules and
  every detail in them become public when copied in. It names the two
  answers: yes copies it in; no keeps loading it at session start, as
  now. A copied-in set is never also opened as an attachment at session
  start.
- **What the leak check adds** (Morgan, 2026-10-19: "Maybe it should also
  run some sort of leak gate to review names of repos etc to make them
  general"): in a repository that is not private, the question also lists
  each line the copy would publish, read the way the leak gate reads a
  push (its word lists, the owners kept private by default, the private
  repositories covered by name) plus the repository's own scrub list. It
  reads only the files a copy brings: the set's `precedent-source.json`,
  its `practices/`, the files those name, and any set it carries. A clean
  set is said to be clean; a check that could not run fully says what it
  missed. It warns and never refuses: the fix belongs in the set's own
  repository, and the person decides. (`copy_in_leaks` in
  [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py);
  test `check_copy_in_question_names_what_would_leak`.)
- **A practice set is never asked.** It is a set, and its sessions read
  the others from their own repositories; asking offered each set a copy
  of itself.
- **How the answer comes back:** `--copy-in NAME=yes|no` (repeated) with
  `--answered-by 'Name, YYYY-MM-DD: "their words"'`, to
  [tools/precedent_update.py](../tools/precedent_update.py) or
  [tools/precedent_install.py](../tools/precedent_install.py). An answer
  with no date or no quote is not recorded. Every set still unanswered is
  printed as a question for the person.
- **What is recorded:**

  ```json
  "copy_in": {"<set>": {"answer": "yes", "answered_by": "Name, 2026-10-19: \"...\""}}
  ```

  A yes also declares the set copied in at `process/<name>`, replacing a
  live declaration of it. **A yes given before the set can be copied**
  (its folder has not reached its own `main`, or there is no clone of it
  on this machine) is recorded with `"waits_on"` saying why, and declares
  nothing; each Update Vendors after that says it is still waiting, and
  the first one that can copy it declares it (Morgan, 2026-10-19, who said
  yes to his voice pack before its owner had Produced it; the declared copy
  with nothing behind it made the update refuse to sync).
  (`copy_in_waits_on` and `copy_in_pending`; test
  `check_early_copy_in_yes_waits_for_the_set`.) For a set that provides the ladder, a yes adds
  it to `binds_everyone` with the same quote; the question says that each
  other code owner should agree first. A no leaves the set arriving the
  way it did before, through the person's own `brings`.
- **The refresh:** every Update Vendors then refreshes each copy from the
  person's clone of the set, with `checkin.py --source`, voice packs
  included, and says how far each one moved (Morgan, 2026-10-20, strength:
  decided: *"Voice packs (and [the writing rules they carry]) should be
  marked to refresh upon a normal vendor update. We should standardize
  these"*). Freezing a copy
  is the repository's call, not the set's: a source entry carrying
  `"hold": "<why>"` in the repository's own `precedent.json` is only
  reported when its origin moves, never counted as behind, and taken this
  once by a run that names it with `--take-set NAME` (the hold, strength:
  assented, Morgan's yes to the proposal). Until 2026-10-20 the set
  declared this itself, `"copy_refresh": "on-go-ahead"` in its
  `precedent-source.json`; a set that still says it is refreshed anyway,
  and the update names the line to delete. The installer copies a yes in
  at once.

The helpers are `copy_in_offers`, `copy_in_question`, `record_copy_in` and
`parse_copy_in_answers` in
[tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py);
the steps are `copy_in_step` and `refresh_copies_step` in
[tools/precedent_update.py](../tools/precedent_update.py). The test is
`check_copy_in_is_asked_once` in
[tools/verify_harness.py](../tools/verify_harness.py).

## A person's own set: the saved copy is for its owner only

A person's individual set cannot be copied into a repository others use:
it holds their name, their zone and how they want to be talked to. In a
private repository the sync has always written its practices into the
tracked `practices/` anyway, as a saved copy, and the tracked AGENTS.md
block carried them for everyone who opened the repository. Since
2026-10-19 (Morgan, strength: assented) the saved copy is its owner's
alone:

- **The record.** When the sync writes individual practices into a
  repository, the individual source's entry in `MANIFEST.json` carries
  `owner`: the set's own `identity.json` GitHub login, name, email and zone.
  A set whose `identity.json` names no login gets no record.
- **The tracked block carries no individual set** in a private repository.
  It is resolved without one, so a slug the set overrides shows the shared
  or universal rule. The set reaches its owner through
  `.precedent/SESSION_PRACTICES.md`, live when it attached.
- **Whose session it is** is the one answer
  `precedent_audience.viewer_and_source` already gives:
  `PRECEDENT_GITHUB_USER`, the person's declared identity, the login this
  clone remembers, then the GitHub account the session's token belongs to.
- **Set missing, the owner's session:** the session file loads the saved
  copy as last known good, and the first reply says so in one line, with
  the date the copy last changed. [precedent_show.py](../tools/precedent_show.py), [precedent_gate.py](../tools/precedent_gate.py)
  and [precedent_paths.py](../tools/precedent_paths.py) serve it. Commits are authored as the owner, in
  their zone: a new rung in [commit-identity.sh](../tools/commit-identity.sh), and the same answer in
  `precedent_identity.commit_env` and `precedent_time`. A check never
  judges a commit against it.
- **Anyone else's session, or one whose person cannot be told, or a copy
  with no owner record:** none of it is read. A slug it holds is answered
  from the declared sources instead, when one has it.

The decisions live in `saved_copy_state`, `withheld_saved_slugs`,
`saved_copy_in_use`, `saved_owner_identity` and `saved_copy_notice` in
[tools/precedent_audience.py](../tools/precedent_audience.py). The test
is `check_saved_individual_copy_loads_for_its_owner_only`, whose negative
control is someone else's session.

**What it does not do:** it governs what a session loads, not who can read
the repository. A file in `practices/` is still there for anyone to open.

## Rolling back

In one repository: point the source back at a sibling clone, drop
`"vendored"`, delete `process/<name>/` and its manifest, and run the sync.
No other repository is touched.
