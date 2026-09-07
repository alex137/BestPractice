---
slug:        reply-links-files
title:       Every reply links the files it touched
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "ending a reply that created, modified or deleted files"
gates:       ["reply"]
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 12
---
## Rule
A session's reply that created, modified or deleted files ends with a
"Files touched" list: each entry links the file on the working branch *and*
its post-merge location, with a one-line description. The reader must be able
to open the work from the chat, not merely learn it exists. **A deleted file
is listed too** — its path, why it went, and a link to the commit that
removed it. It is the one entry with nothing to open on the branch, which is
exactly why a reader will not find it on their own.

## Detail
**A deletion is linked at the commit that made it**, not on the branch: a
branch link to a path that no longer exists is a 404, and the reader wants
the diff anyway — the removing commit shows what went, in full, and keeps
the content one click away for as long as the history exists. A whole
retired directory is **one entry**, named as the directory with a file
count, never one line per file; the point is that the reader can see what
left, not that they can count it. Where the deletion is a retirement
([retirement-deletes-files](retirement-deletes-files.md)), the reason the
audit was given is the reason this entry states — write it once and use it
in both places.

**Rendered files get a rendered-view link, not just a repo link.** A
repository link to an HTML file or an image shows source or a raw blob — the
one form of the file the reader did *not* want. When the session's surface
offers hosted private previews (an artifact/paste service the harness
provides), a touched HTML render or picture's entry also carries that
rendered-view link, published from the same file path each time so the link
stays stable across revisions — one preview per file, re-published on
meaningful change, never a new one per reply. Files that are per-recipient
send records are excluded: a hosted preview is a distribution channel, and
those files' distribution is governed by their own send policy.

## Why
A reply that names the files it changed tells the reader that work happened. A reply that links them lets the reader open the work. The difference is one search per file per reply, paid by the reader every time -- and paid by the person with the least context, since the writer already has every path in hand.

Both links are required because each goes dead at a different, predictable moment. The working-branch link is the one that resolves now, while the reviewer is looking at the branch; the post-merge link is the one that still resolves after the branch is deleted.

Deletions are listed for the opposite reason to everything else in the list: not because the reader cannot open them easily, but because they cannot find them at all. A created or modified file announces itself — it is in the tree, and anyone browsing the branch trips over it. A deleted one leaves nothing behind to trip over, so a reply that omits it has hidden the single change the reader is least able to reconstruct, and the one most likely to be the one they would have objected to.

## Story
**This practice had an empty `## Why` as well as an empty `## Story`** --
the only one in the catalogue with neither, which is how it stayed
unnoticed: nothing looks wrong about a short file. The reason is recorded
here rather than left blank in both places.

No dated incident was recorded. What the rule prevents is a small cost paid
constantly rather than a large one paid once. A reply that names the files
it changed tells the reader that work happened; a reply that links them lets
the reader open the work. The gap between those two is one search per file
per reply, paid by the reader, forever -- and the writer, who already has
every path in hand, is the one person for whom closing it is free.

**Both links are required for a reason.** The working-branch link is
readable now, while the branch still exists and the reviewer is looking at
it; the post-merge link is the one that still resolves in a year, after the
branch is deleted. Either alone goes dead at a predictable moment.

**Deletions were added 2026-09-07**, on Morgan's ask, the same day
[retirement-deletes-files](retirement-deletes-files.md) landed and made
deleting a routine act rather than a rare one. Before that the rule said
"created or modified", so a session that deleted a directory could satisfy
it completely and never mention the deletion — and the practice that had
just been written to make deletion normal would have made that omission
normal too.

## Install
Convention in
[templates/AGENTS.md.template](../templates/AGENTS.md.template).
