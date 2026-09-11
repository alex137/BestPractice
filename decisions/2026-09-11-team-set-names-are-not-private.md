---
date: '2026-09-11'
question: |
  The leak gate notes, on every run that loads the private
  blocklist, that no pattern matches the bare names of two team
  practice sets -- only their owner-qualified forms are refused.
  The note reads as a gap to close. Should a pattern be added for
  the short form people actually type?
decision: |
  No. The team practice sets' names are not private, and neither
  is the account that owns them. Morgan, 2026-09-11, asked whether
  to add the patterns: "I don't care if the names leak". Nothing
  is to be added to the blocklist to catch the bare forms, and a
  future session finding that note should read this record rather
  than re-deriving the question. What IS still open is the shape
  of the rule itself -- see TODO.md's `repo-name-regex-shape`.
alternatives: |
  ["Add a bare-name pattern for each set, as the gate's own note
  suggests -- rejected on measurement: `precedent-team-writing`
  appears 25 times in this tree and `precedent-team-working-style`
  13, in precedent.json (which must declare each source by name),
  practices/source-naming.md, spec/SOURCE_NAMING.md, TODO.md and
  the document-project templates. A pattern would refuse 38
  references that are correct and necessary.",
  "Add the pattern and carve out the legitimate files by path --
  rejected as the wrong lever: it would make the gate agree with
  itself by exception rather than record that the name is not a
  secret, which is the actual fact.",
  "Leave the note unanswered and let each session decide --
  rejected because that is what produced the wrong advice this
  record corrects: a session recommended adding stems before
  measuring what they would hit."]
decided_by: Morgan
strength: decided
---

## Why this was asked

The private blocklist declares an owner private-by-default, so any
`owner/name` mention of a repository under that account is refused unless an
`allow` line names it. **That layer only ever sees the owner-qualified
form.** A bare `precedent-team-writing`, with no owner prefix — which is how
anyone actually writes it in prose, in a clone path, or in a `precedent.json`
source declaration — matches neither that layer nor any plain pattern in the
list. The gate says so on every run, as a note rather than a hit.

Two real leaks the same day made the note look urgent. Both were
owner-qualified, both were caught, and both were in
[spec/SOURCE_NAMING.md](../spec/SOURCE_NAMING.md)'s row-1 example, arriving
in separate commits hours apart from sessions that could not read the
blocklist. The reflex after catching those was to close the bare-name gap
too.

**The reflex was wrong, and measuring it is what showed that.** The bare
names are already in this public tree 38 times, and nearly all of those are
load-bearing: a shared repository declares its team sources by name, and the
naming convention is documented with real examples. A pattern would turn the
gate red on the repository's own correct declarations.

So the honest resolution is not a pattern but a fact, stated once: these
names are not secret. That matches how the same question was already settled
for the retired personal pack, whose `allow` line carries Morgan's own words
from 2026-09-07 — *"the name isn't private, I don't care if the name is
leaked"* — and it is the same answer, two days later, for the team sets.

## What this does not settle

**Whether the owner-qualified rule is the right shape at all.** It refuses
`owner/name` and ignores `name`, which means the gate's coverage depends on
a formatting choice the writer did not know they were making. That is a real
question about the mechanism, and it is deliberately left open here rather
than answered in passing — [TODO.md](../TODO.md)'s `repo-name-regex-shape`
item holds it.

**The blocklist's own copy of this decision.** The list lives in a private
repository this session could read and not write. Adding an explanatory
comment there is optional and can ride along the next time a session is
rooted in that set; nothing depends on it, because the decision is recorded
here and the gate's behaviour does not change either way.
