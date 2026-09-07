---
slug:        document-status-header
title:       A spec or record document declares its kind and status in frontmatter, not in prose
tier:        on-demand
severity:    default
applies_to:  ["spec/**/*.md", "record/**/*.md"]
occasion:    "creating, migrating, closing or superseding a document under spec/ or record/"
gates:       []
index_clause: "kind and status in frontmatter; a reader must not have to infer either"
checked_by:  "tools/precedent_check.py"
defines:     ["document kind", "document status"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-07"
approved_by: "Morgan (2026-09-07)"
---
## Rule
Every document under `spec/` and `record/` opens with frontmatter declaring
what **kind** of document it is and what **state** it is in, so a reader knows
in three seconds whether they are holding a live reference or the record of
something that finished. The fields are `title`, `kind`, `status`, `opened`,
`closed`, `superseded_by`, `supersedes`, `audience`, `summary` — the full
schema, and the legal `status` values for each `kind`, are in
[spec/DOCUMENT_LIFECYCLE.md](../spec/DOCUMENT_LIFECYCLE.md).

**The kind decides what "outdated" can even mean for the file.** A
`reference` states how the system works and can become wrong. A `record` is a
true observation of a date and stays true forever — a measurement's "52
practices" is not stale, it is the condition the measurement ran under.
Marking both with the same freshness idea is what makes a reader distrust the
wrong one.

Three obligations follow, and the third is the one migrations lose:

1. **Creating** a document under either tree means stamping it in the same
   commit. Nothing else has to be true for the header to be writable.
2. **Closing** work means setting `status` and the `closed` date, in the
   commit that closes it — not in a later tidy-up pass.
3. **Replacing** a document means setting the old one's `status: superseded`
   and `superseded_by`, and the new one's `supersedes`, in the commit that
   lands the replacement. A migration that moves, splits or rewrites
   documents is exactly when this is skipped, because the new document feels
   like the whole job. Pair this with
   [index-remembers-past](index-remembers-past.md), which puts the lineage in
   the index; this puts it in the files.

**Do not declare a status in prose as well.** A bolded "Status: …" opening
line is a second, hand-maintained copy of a field a check can read, and it
decays independently of the thing it describes. Same for a `Last updated:`
comment: version control answers *when did this change* losslessly, and for
the `brief` and `record` kinds, where the date genuinely is the subject, it is
carried by `opened` and `closed` where a check can reach it.

## Why
A document's status is *already* being recorded — the question is only
whether it is recorded somewhere a machine can read. Left to prose, it gets
written in as many formats as there are authors, and every one of them is a
hand-maintained second copy of a fact that changes independently of it. The
copy does not update itself, so it does not merely fail to help: it decays
into asserting the opposite of the truth, and a closed brief that still reads
"not closed" is worse than one that says nothing at all.

The cost lands hardest on exactly the reader the repository cannot afford to
lose — someone arriving cold, human or a fresh session, who has no way to
tell a live normative reference from the record of a phase that finished
weeks ago. They then either read all of it, at full cost, or guess. A
directory listing of thirty files gives them nothing to guess with.

Putting the claim in frontmatter is not merely tidier. It makes the claim
**checkable**, and a checked claim is the only kind that stays true: the
same field a reader sees is the field a gate reads, so the two cannot drift
apart the way a banner and a table can. It also makes the whole tree
derivable — an index of what is open, what is superseded and what is current
becomes generated output rather than a hand-maintained list that is itself a
new drift surface.

The `kind` field carries its own weight, separate from `status`. Without it,
a freshness rule has to treat a reference document and a dated measurement
identically, and one of the two will always be marked wrongly.

## Story
Twenty-four documents accumulated under one repository's `spec/`, and status
was already being recorded in all of them — in six mutually incompatible
prose formats, owned by nobody. One opened *"Status: phase 3 is fully
closed"*; another *"Done, 2026-09-01"*; another *"Status: opened 2026-09-03,
not closed"*. A closed phase brief and a live normative reference were
indistinguishable from the file listing, to a visitor and to a cold session
alike.

The recency stamps were worse than uninformative. Every one of those files
opened with `<!-- Last updated: DATE -->`, a marker that cannot distinguish
*finished on that date* from *stale since that date* — opposite meanings,
identical rendering. On 2026-09-07 one of them read `Last updated:
2026-09-07, run in progress` in the very commit that closed the run and
marked all four of its passes done: the session updated the table and not the
stamp, because nothing checked the stamp and nothing derived from it. **A
hand-maintained status marker is not merely uninformative; it goes on
asserting the opposite of the truth.**

The backfill that landed this rule found the same drift a second time, in the
other direction: a plan whose prose still said *"drafted, not executed"* had
had its first two steps executed two days earlier. Neither error was anybody's
carelessness. Both were the predictable result of storing a claim somewhere no
check could read it.

## Install
Add frontmatter to every document under `spec/` and `record/` with the schema
in [spec/DOCUMENT_LIFECYCLE.md](../spec/DOCUMENT_LIFECYCLE.md), and delete the
prose status sentence and any `Last updated:` comment in the same commit —
leaving both is how the two copies start disagreeing. Stamp one file first
and run the check across the whole tree in `--warn-only` mode to see the real
violation count before committing to it; a standard that fails twenty files
on the commit that introduces it is a standard people switch off.
[tools/doc_lifecycle.py](../tools/doc_lifecycle.py) is the check, registered
in [tools/precedent_check.py](../tools/precedent_check.py); flip it to
blocking once the backfill is done.

Two traps, both hit for real on the way in. Quote any `title` or `summary`
containing a colon-space — unquoted, YAML reads it as a nested mapping and
the frontmatter silently parses into the wrong shape. And write the
`Last updated:` detector to require the comment delimiter, after stripping
fenced blocks and code spans: a plain substring match fires on the document
that documents the rule, which teaches its first reader that the checker is
broken.
