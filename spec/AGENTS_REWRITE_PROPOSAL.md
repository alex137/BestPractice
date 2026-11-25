---
title:         Proposed Hand-Written Text For AGENTS.md
kind:          proposal
status:        executed
opened:        2026-11-25
closed:        2026-11-25
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "The hand-written half of AGENTS.md rewritten to say what is true now, by role, with no names, dates or history. Accepted and carried out on 2026-11-25; AGENTS.md now holds this text."
---
# Proposed Hand-Written Text For AGENTS.md

This is the hand-written half of [AGENTS.md](../AGENTS.md), rewritten under [record-not-instruction](../practices/record-not-instruction.md). The generated half, the resident rules and the occasion index, is not shown and does not change, except that its heading loses its token and practice counts.

## What Changes

| Today | Proposed |
|---|---|
| Opens with whose sign-off a merge does not need, who relayed it, two dates and a quoted question | States the rule: a session may merge into the landing branch once its check passes |
| Lists nine spoken commands with a paragraph each, and the occasion index lists the same commands again | One sentence pointing at the index, which already carries each command and what it does |
| Session setup names environment variables and retells the long form | Three sentences and a link to the setup page |
| "Restructured from BestPractice by the plan of record (phases 0-7, merged into main on a date)" | "This repository is Precedent", and where its format and loader are described |
| A table row about what may be raised "with Morgan" | "with the person" |
| The gotcha section explains three times that nothing loads the catalogue | Two sentences |
| A schedule line quoting who approved it and when | The schedule and what a commit that changes it must update |
| A line about a migration on a date | The rule that is left: new items go under `todo/` |

By rough count the hand-written half goes from about 14,700 characters to about 6,800. Every link the current text carries to a practice or a tool is kept, except the links to history.

## The Text, Above The Generated Half

```markdown
# Repository notes for agents

**Pull requests.** Every pull request targets your landing branch.
`python3 tools/precedent_branches.py --landing` says which it is: check it,
and never assume the repository's default branch. A session may merge its own
pull request into the landing branch once the push check passes; no sign-off
is needed. Where the landing branch is `main`, merge without waiting for the
full suite: GitHub's check reports afterwards, and the session fixes what it
reports. A merge is done when a fetch shows the content is there
([verify-postcondition](practices/verify-postcondition.md)).

**Spoken commands** are the first entry of the occasion index below.
Recognise one by what the message asks for, not by a keyword
([read-for-intent](practices/read-for-intent.md)), load its practice before
acting, and confirm a hard-to-reverse reading out loud.

**Session setup.** Session start attaches the practice sources this
repository declares ([PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md)).
If it reports one missing, attach it
([attach-never-clone-individual](practices/attach-never-clone-individual.md)),
then run `python3 tools/precedent_session_check.py` and follow a failing
row's own remedy. A session rooted above the repositories it works in runs
none of their hooks; `python3 tools/precedent_run_session_hooks.py` runs them
by hand.

**This repository is Precedent**, the practice layer other repositories
install. [MAP.md](MAP.md) is the map,
[spec/PRACTICE_FORMAT.md](spec/PRACTICE_FORMAT.md) the practice-file format
and [spec/LOADER.md](spec/LOADER.md) the loader.
[spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md) says why a
mechanism exists.
```

## The Text, Below The Generated Half

```markdown
**Orientation: read [MAP.md](MAP.md) first.** [README.md](README.md) is the
pitch for people. The practices you follow here are the ones this repository
teaches.

## Where things are

Check here before searching. The full index is
[WHERE_THINGS_ARE.md](WHERE_THINGS_ARE.md); both tables are generated from
[where_things_are.json](where_things_are.json), so a row is added or changed
there.

(the generated table, with "may be raised with the person" in place of the
name, and "Repo map, generated" in place of "generated (phase 2)")

## Environment traps

Traps are catalogued one file each under [gotchas/](gotchas/), with an
overview at [gotchas/INDEX.md](gotchas/INDEX.md). Nothing loads them for you:
on a failure you cannot explain, search there first
(`grep -ril '<a word from what you see>' gotchas/`). A new one is written as
`gotchas/gotcha-<date>-<slug>.md`, then `python3 tools/build_gotcha_index.py`
([environment-gotchas](practices/environment-gotchas.md)).

## Working in this repository

- **Not running under Claude Code?** Run `bash tools/bootstrap.sh` at session
  start ([templates/harness/README.md](templates/harness/README.md)).
- **One schedule is in force:**
  [deep-check.yml](.github/workflows/deep-check.yml) runs the whole suite
  daily at 07:17 UTC. A commit that adds, changes, pauses or removes a
  schedule updates this line.
- **A check-in pull request from a dependent repository gets a second
  scrub.** Challenge any name, number or incident detail that reads as that
  repository's own before merging, and have it added to the contributor's
  blocklist ([INSTALL.md](INSTALL.md), section 4).
- **Edit directly** what is about this repository: its README, practice
  wording, engine code. A lesson learned elsewhere arrives by a scrubbed
  check-in from where it was learned.
- **Open items go under [todo/](todo/)**, one file each. The root
  [`TODO.md`](TODO.md) is a redirect, and the deep check refuses an item
  added to it.
- **After touching the deck engine**, rebuild the sample both ways:
  `python3 deck/build_deck.py deck/sample` and `--send`.
- **Two check levels** ([two-check-levels](practices/two-check-levels.md)).
  The light check is `python3 tools/doc_lint.py` on the Markdown you touched,
  before every commit. The deep check is
  `python3 tools/precedent_push_check.py`, run bare, before a push or a
  merge; it takes seconds. The full suite is
  `python3 tools/precedent_branches.py --run-tests`, and GitHub runs it after
  a push into `main`. What matters is `0 failed` and `0 violated`.

## Conventions

- **Documents for outside readers use the reader's words**
  ([readers-vocabulary](practices/readers-vocabulary.md)), checked in a pass
  of its own: the README, [SETUP.md](SETUP.md) and
  [templates/GETTING_STARTED.md](templates/GETTING_STARTED.md).
- **A built deck is delivered** ([deck/README.md](deck/README.md)): attach
  the HTML to the reply that builds it, and send only the `--send` build
  outside.
```

## What Is Left Out, And Where It Still Is

- **Who authorized merging without sign-off, and when.** In the history of this file, and it belongs in the approval line of the practice that governs landing.
- **The long form of each spoken command.** In each command's own practice, and in [AGENTS_COMMANDS_IN_FULL.md](AGENTS_COMMANDS_IN_FULL.md).
- **The environment variables session setup reads.** In [PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md).
- **How the pass receipt works and how to turn it off.** In [AGENTS_COMMANDS_IN_FULL.md](AGENTS_COMMANDS_IN_FULL.md#two-check-levels).
- **The joke that a session skipping the practices here is the joke writing itself.** Dropped.

## What Has To Be Checked Before It Replaces The Current Text

Some checks read AGENTS.md for particular words, as the one for "Drop it" does. Each has to pass on the new text, or be shown to be reading history that has moved.
