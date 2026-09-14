---
slug:        migration-scrubs-vocabulary
title:       A migration scrubs the old system's vocabulary immediately, not on request
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "migrating a repo off an old practice system onto Precedent"
gates:       []
index_clause: "scrub the old system's vocabulary the same session, not on request"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "pending review"
---
## Rule
When a repo migrates off an old practice system, every day-to-day
document — instructions file, glossary, map, onboarding page, workflow
comments — is scrubbed of that old system's names, retired workflows, and
now-dead concepts in the **same migration**, not left for someone to
notice and ask for later. The old vocabulary survives only in the
dedicated migration record and genuinely historical logs (decision
records, dated brainstorm journals) — declared explicitly, once, never
decided ad hoc per file.

## Detail
"Scrub" here means the same thing [spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md)'s
own step 5 already asks for the old tree's file *paths* — replace the
teaching of a dead concept with a statement of current fact, pointing at
the migration record for anyone who wants the history — generalized past
paths to every proper noun, retired secret name, and dead workflow
description the old system left behind. A document that still spends a
paragraph explaining what the old system *was* before stating what's true
now has not finished migrating; it has migrated the mechanism and left
the prose behind.

**Declare what counts, once, rather than deciding per file:**
`process/retired_vocabulary.json` at the migrated repo's root lists the
retired terms (proper nouns, secret names, path fragments — literal
substrings, matched anywhere) and the files exempt from the scrub (the
migration record itself, plus any file that is *explicitly* a historical
log by its own stated purpose — a decision-record directory, a dated
brainstorm journal — never a file merely because it happens to be old).
Everything else in the tracked tree is fair game, and a retired term
found outside the exempt list is real, unfinished migration work, not a
style nitpick.

An `exempt_files` entry ending in `/` exempts a whole directory rather
than one file — for exactly one case: a *materialized*, regenerated
directory (this repo's own `practices/`, wherever
[tools/precedent_materialize.py](../tools/precedent_materialize.py) fills
it in from a repo's declared sources) can legitimately hold *other*
repos' own content, which isn't this repo's own migration to finish and
whose file list changes on every sync — hand-listing it file-by-file
would go stale the moment a slug is added or dropped. Reach for a
directory exemption only for a materialized directory, never as a
shortcut around scrubbing a repo's own hand-authored tree.

## Why
Asked directly whether cleaning up old-system vocabulary had happened as
part of a real migration, the honest answer was no — it took a separate,
later question to notice and fix. By then the vocabulary had already sat
in a session's primary instructions file for a day, teaching a system
that no longer existed to every session that read it in between. Nothing
about that gap required the second question; the first migration had
every fact it needed to do the scrub itself, in the same sitting.

## Story
`themorgan/WorkingWithAI`'s migration off RepoPersonalPreferences
(2026-09-02) split the old vendored pack into the new team/individual
sources correctly, but left the old pack's name, its retired secret
(`PERSONAL_PACK_TOKEN`), and a paragraph explaining what the old
scheduled sync used to do scattered across `AGENTS.md`,
`GETTING_STARTED.md`, `GLOSSARY.md`, `MAP.md`, and three
workflow-configuration-file (YAML) headers. It was a day before anyone asked whether that vocabulary was
still needed; the honest answer, once asked, was no — none of it. The fix
was mechanical once someone looked (`grep` for the old names, keep the
migration record's own mentions, trim everywhere else), which is exactly
why it belongs in the migration pattern itself and behind a real check,
not in a person's memory of to ask about it eventually.

A second, different migration (`themorgan/HavrutaBrainstorm`, 2026-09-03)
ran the check for real and found two bugs in the check itself, not in the
migration: the check's own `ROOT` resolved wrong once vendored at
`process/upstream/tools/precedent_check.py` (it silently scanned
`process/upstream/`'s own tree instead of the migrated repo's, reporting
a false-clean `SKIPPED`), and a real retired term
(`RepoPersonalPreferences`) collided with team-set content this same
migration's own `precedent_materialize.py` step had just copied in —
unrelated to this repo's migration, since it was that other source's own
legitimate provenance note. Both are fixed as of this writing (the `ROOT`
fix, and the directory-exemption support in Detail above); this Story
entry is the record that they were real, not hypothetical.

## Install
`tools/precedent_check.py`'s `migration-scrubs-vocabulary` check reads
`process/retired_vocabulary.json` (absent = `NotApplicable`, the correct
state for a repo that has never migrated off anything) and scans every
tracked file outside its `exempt_files` list (files and, since 2026-09-03,
`/`-suffixed directories — see Detail) for any declared term, outside
`process/upstream/` (a byte-identical vendored copy, never hand-edited
regardless). [spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md)'s
step 5 is where a migration declares the file and runs the check for the
first time, before the migration is considered done. `ROOT` resolves via
`git rev-parse --show-toplevel` (matching `doc_lint.py` and
`practice_audit.py`), which is what makes the check see the *consuming*
repo's own tree correctly whether this file is running self-hosted or
vendored at `process/upstream/tools/`.
