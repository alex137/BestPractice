---
slug:        built-from-is-checked
title:       A copy built from another copy records what it was built from, and the update checks it
tier:        on-demand
severity:    default
applies_to:  ["tools/precedent_update.py", "tools/precedent_update_all.py", "tools/precedent_regenerate.py", "spec/VENDORED_SHARED_SETS.md", "**/BUILT_FROM.json"]
applies_to_why: "The mechanism lives in the update and its spec, and in each BUILT_FROM.json a source exports; a session editing any of them is the one that can break the comparison. Decided: 2026-11-01, with the practice."
occasion:    "a source exports files it compiles from a source of its own, or a repository copies in both"
gates:       []
index_clause: "compiled files record inputs by content; update refuses DONE on a mismatch"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-11-01"
approved_by: "Morgan, 2026-11-01 -- asked whether a repository copying a voice and the writing rules got the rules twice and whether the copy inside the voice stayed current, had the plan reviewed by a second session, then \"Implement your plan, act and booked\""
strength:    decided
---
## Rule
**When a source exports files it compiles from a source of its own, it
exports a record of what they were built from**: every input and its git
blob hash, naming the copied-in source an input sits in. **Update Vendors,
in a repository that also copies that source in directly, compares the two
and refuses DONE while they differ**, naming the repository to update
first. Record content, never commits: most of a source's commits never
touch what a compiled file read.

The building repository lists the compiled files as generated, with their
inputs, so its own update rebuilds them; the tool that writes them writes
those entries. Update All Vendors runs a repository after every one it
copies from.

## Detail
The record is `BUILT_FROM.json`, exported beside the compiled files; its
shape, and how each piece of the engine reads it, are in
[spec/VENDORED_SHARED_SETS.md](https://github.com/alex137/BestPractice/blob/staging/spec/VENDORED_SHARED_SETS.md),
"A source built from another source". A held copy is reported, never left.
A file the consuming repository does not hold is not compared.

**The two copies stay.** The direct copy is what the consuming repository's
own tools read; the compiled one exists to be used where no repository
stands behind it. Neither is removed to make the problem go away: the
record makes it visible, and the update order makes it rare.

## Why
A consumer that copies both gets the inner source by two routes of
different length. The direct copy moves in one update; the compiled one
moves only after the building repository updates, rebuilds and lands.
Without a record of what the compiled files were built from, nothing can
tell when they lag, and an update reports DONE over two copies that
disagree.

## Story
2026-11-01. A repository copied in a voice's compiled prompts and, beside
them, the writing-rules set the prompts were compiled from. Asked whether it
held the rules twice and whether the copy inside the prompts stayed current,
a session found three copies, all current that day only because every
repository had updated within a day of the rules' last change. The compiled
prompts named their source files but no version, and Update All Vendors ran
repositories in the order typed. A second session reviewed the plan and
changed it: blob hashes instead of commits, which would have refused DONE
for most of the source's commits; the rebuild step Update Vendors already
had, instead of new code; and the record as an exported file, not a header.

## Install
Nothing to install: the engine reads any `BUILT_FROM.json` a copied-in
source exports. A source that compiles files from another declares the
record in its `exports` and has its build tool write it.
