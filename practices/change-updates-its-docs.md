---
slug:        change-updates-its-docs
title:       A change updates the documents that describe it, in the same commit
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "changing a mechanism, a workflow or a behaviour that some document describes"
gates:       ["merge"]
index_clause: "update the document that describes it, in the same commit -- never later"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08"
---
## Rule
**When you change how something works, update the document that describes it
— in the same commit as the change, not in a follow-up.** A tool that gained a
flag, a command whose meaning moved, an install step that is now one step
instead of two: whatever a reader would have been told, tell them now.

**And when you add something a person is expected to know about, put it where
that person reads.** A feature documented only in a specification the audience
never opens is a feature nobody has.

Finding the document is part of the change, not a separate task. Search by
purpose as well as by mechanism ([search-by-purpose](search-by-purpose.md)):
the page that describes your tool may never name it.

## Detail
**Same commit, and the reason is not tidiness.** A documentation update
deferred to "after this lands" competes with whatever lands next, and loses.
More than that, the commit is the only place where the two halves are
provably about the same change — split them and a reader six weeks later has
a document, a diff, and no way to tell whether one explains the other.

**Not every change touches a document.** A refactor nothing describes, an
internal rename, a test: none of these has a reader-facing half. The question
is *what would somebody have been told*, and often the honest answer is
nothing.

**The generated views are not this rule's business.** `AGENTS.md`, `MAP.md`
and `GLOSSARY.md` are rebuilt from the tree by
[tools/build_views.py](../tools/build_views.py), and hand-editing them is a
separate violation ([generated-artifact-provenance](generated-artifact-provenance.md)).
This rule is about the prose a person wrote.

**The occasional sweep is a backstop, not the mechanism.** The registry at
[tools/doc_coverage.json](../tools/doc_coverage.json) records what each
reader-facing document describes, and `very deep check` compares each
document's last commit against the last commit touching its subject. That
catches what this rule missed, weeks later, with the evidence attached — but
a finding there means the rule was already broken. It is deliberately a list
to read rather than a gate to pass, because a document older than its subject
is often perfectly correct and no script can tell that from a real omission
([fail-gracefully](fail-gracefully.md)).

That registry has its own obligation: a reader-facing document nobody lists
is a document the sweep cannot see, so the sweep reports those too.

## Why
A rule about the outside world goes stale silently
([volatile-rules-carry-dates](volatile-rules-carry-dates.md) is the same
worry, narrower). A document about *this repository* goes stale in exactly
one way — somebody changed the thing and left the description alone — and it
is invisible at the moment it happens, because the person making the change
already knows the new behaviour. **The reader who finds out is the one least
equipped to tell whether the document or the code is wrong.**

Stale documentation is worse than none. Absent documentation makes a reader
go and look; wrong documentation makes them confidently do the wrong thing,
and it costs them the time to discover that too.

## Story
**Raised by Morgan, 2026-09-08**, looking at `documentation/` after several
days of heavy change: *"very-deep-check should update the documents according
to what's changed. (Also, if it doesn't already, any change should update the
documents that document that change; very-deep-clean is just an occasional
check.) Note that this should also check to make sure the features that are
important for humans to know are documented."*

Both halves of that are in this rule, and the ordering is his: the standing
obligation is the change's own, and the sweep is a backstop. A repository
that relies on the sweep has decided to find out about its stale documents
weeks late, in a batch, which is how they get fixed in a batch — badly.

**The sweep found five documents behind their subjects on its first run**,
including two of the four public-facing guides. Nothing had gone wrong that
anybody would have noticed; each was a change that had reached the code and
stopped there.

The "features humans need to know" half got a narrower, mechanical answer
than the phrase suggests: every phrase a person is expected to *say* — the
capitalized entries in any active practice's `defines:` — has to appear
verbatim in the page that teaches the vocabulary. That is checkable, and it
is the half that fails silently, because a command nobody was told about
produces no error at all.

## Install
**`checked_by` is deliberately null.** The sweep exists and is real, but its
findings are prompts a person answers, and wiring that into the enforced
channel would make a red gate out of a question — which is how a check
becomes the one people pass by editing the registry. `very deep check` runs
it; nothing else has to be installed. A
repository that wants it needs
[tools/doc_coverage.json](../tools/doc_coverage.json) listing its own
reader-facing documents and what each describes — without that file the sweep
says so and does nothing, which is the correct behaviour for a repository
that has not declared any.
