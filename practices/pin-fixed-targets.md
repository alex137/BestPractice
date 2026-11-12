---
slug:        pin-fixed-targets
title:       A step that reads the same thing every time pins it by ID
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus that covers it honestly. The steps this governs are written wherever a project keeps its repeatable work -- a repo-local command's practice file, a runbook, a script's config, a scheduled task's prompt, an agent brief -- and the last two leave no file in the tree at all. A narrower glob would hide it at exactly the moment a command is written into a place the glob missed, so the occasion index carries it. Decided: 2026-11-12, when the practice was written."
occasion:    "writing or running a step that reads the same file, folder, page, view or channel every time"
gates:       []
index_clause: "pin it by ID in one place; search only for what is new, then fix the pin"
checked_by:  null
defines:     ["pin"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-11-12"
approved_by: "Morgan, 2026-11-12, asked for it as a universal practice; relayed to the session that wrote it by another of his sessions (session_01Xcy6U3mHUtmgcGNqRZSX8m), which drafted the rule and its first subtleties. Landed on his own word in this session, 2026-11-12: \"booked\". Decided: he asked for the practice himself."
strength:    decided
---
## Rule
**A step that reads the same file, folder, page, view or channel on every
run names it by its ID** -- the pin -- and never finds it again by title.
Two runs a month apart would want the same object: that is the test. A
step whose answer depends on what happened since the last run (new notes,
new mail, new rows) is discovery, not a fixed target, and searches -- but
inside a pinned container, never across the whole service.

**Writing the step, resolve the target once, then and there**: search, and
if more than one candidate turns up, ask the person which one. Write the
pin into the step: the ID, the title it had, and the folder or parent it
lives in ("What a pin holds").

**Running it, read the pin, and check what came back** against the title
and parent it records, and against any successor note or archived state
("A pin that still opens"). **A pin that fails or looks superseded gets one
search; then the pin is fixed in its one place, committed, and said in the
reply.** A search that finds two candidates, or none, stops and asks; it
never picks.

**A target that rolls over each period** (a quarterly sheet, a yearly
folder) pins the parent and the naming pattern, never this period's file
("Per-period targets").

**A pin lives in one place** that every step using it points to
([registry-source-of-truth](registry-source-of-truth.md)): inline in the
step while one step uses it, in one config file once a second does. **A
tool shared across projects reads its pins from that config**, never from
its own code ([engine-plus-host-shims](engine-plus-host-shims.md)).

**A link that grants access by itself is a credential**, and stays out of
a public repository ("Links that are keys").

## Detail
### What a pin holds
The ID, not the URL, where the service has one: a URL can change its
shape, gain a tab or a view parameter, or carry a share key; the ID
survives a rename and a move. Beside it, the title it had when pinned and
the folder, database or workspace it sat in. Those two are not lookup
keys; they are what the run checks the result against. Add a cadence when
there is one ("written daily by the form"), because that is what lets a
run notice a pin that went quiet.

Example, one line in a command's first step:
`Sheet: 1AbC...xyz ("Survey responses", in "Intake / 2026"), written daily.`

### A pin that still opens
A pin can be wrong while it works: the file opens, but it was superseded,
renamed to "OLD", moved to an archive folder, or replaced by a copy the
team now writes to. The run already has the metadata in hand, so the check
costs nothing extra. Treat the pin as stale when any of these is true:

- the title now carries a marker the pin did not: *old*, *archived*,
  *deprecated*, *superseded*, *do not use*, *copy of*;
- it sits in the trash, an archive, or a parent other than the one
  recorded;
- the top of the file, or its description, points at a successor;
- the pin records a cadence and the last edit is well outside it.

Without a recorded cadence, skip the last test: a reference document
edited once a year is not stale for being old. A stale pin takes the same
path as a dead one: one search, scoped to the recorded parent first, then
the fix, or the question.

### Fixing the pin
Fix it where it lives, in the same session, and commit it
([repo-is-memory](repo-is-memory.md)); the reply names the old title, the
new one and why. A run that cannot write the file -- an unattended job, a
session without push access -- uses the result for this run only and
files or updates an issue saying what it found
([automation-issues](automation-issues.md)), so the next run does not
search again unawares.

### Per-period targets
"This quarter's tracker" is the same file only until the quarter ends.
Pin the folder that holds each period's file and the pattern its name
follows, and resolve the period's file by listing that folder, not by
searching the service. When this period's file is not there yet, say so;
never fall back to last period's silently. Pinning a period's file
directly is fine when the step says when it rolls over and who fixes it.

### What may stay unpinned
**A lookup may stay unpinned when the service itself guarantees a single
answer**: an exact key the system enforces as unique (a repository by
owner and name, a user by email, a workspace by its slug), resolved in
one cheap call. A title search never qualifies, because titles are unique
only by habit, and a lookalike, a copy or a renamed file is exactly what
it returns. Plain code making that one call at start-up needs no pin;
the same lookup written as a step a session reads and redoes by hand is
still a pin worth writing, because the session pays for it in reading.

### Scope
Any step something follows more than once: a repo-local command, a
runbook, a scheduled task's prompt, a script's configuration, and a brief
handed to an agent that will be reused. A one-off brief for a single run
needs no pin; if it will be pasted again, it does.

### Links that are keys
Some links open the thing for anyone who holds them: a share key in the
URL, a file shared to anyone with the link (where the bare ID is then the
key), a webhook address. In a public repository the step names the pin
and says where it is kept -- the project's private config, an individual
set, an environment variable -- and never carries the value
([private-repo-scrub](private-repo-scrub.md)). An ID that only opens for
someone already granted access is not a secret, but in a public
repository even that can say a private thing exists; when it would, it
goes to private config too.

### Why no check
Tried and declined, for a specific reason
([checkable-gets-checked](checkable-gets-checked.md)): whether a target is
fixed or new is a question about meaning, and the lexical shapes a check
could match ("search the folder", "find the latest") are shared by
discovery steps, which are correct. The commands this governs also live in
consuming repositories, most of them private, so a check here would run
against a tree that holds none. The occasion index carries it; a project
whose commands share one format could check that each names an ID-shaped
token in its first step.

## Why
A search by title costs a lookup on every run and can return the wrong
file: a copy, a lookalike, or the superseded version a team stopped
writing to. A pin costs one lookup, once, and a cheap check on each read
catches the case where it still opens but should not be trusted.

## Story
**2026-11-12, a daily command in a private project repository.** Its
command for pulling the results of a personality-profile questionnaire
told each session to read "the spreadsheet linked to" the questionnaire's
form, and gave neither a link nor an ID. So every run, every day, first
searched the drive by title to find the same file. That cost a lookup on
every run, and could as easily have landed on a copy or a renamed
lookalike as on the sheet the form writes to. The fix put the sheet's
link and ID in the command's first step, with a search kept only as the
fallback.

A review of the same repository's other commands found that the rest
already pinned their fixed targets -- drive folder IDs, a database view
ID, the customer-relationship (CRM) system's owner IDs -- and that their remaining searches were all for
new things, such as meeting notes added since a bookmark. That split, a
pin for what is the same each time and a search for what is new, is the
rule. Morgan asked for it as a universal practice the same day, and added
the case a dead-link fallback misses: a pin that still opens, but onto a
file that has been superseded.

## Install
Nothing to install. Where a project's commands share one format, put each
fixed target's pin in the command's first step, or in the one config file
its commands read once two of them share a target.
