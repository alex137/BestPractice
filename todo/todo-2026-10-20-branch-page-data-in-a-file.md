---
slug:              todo-2026-10-20-branch-page-data-in-a-file
kind:              manual
domain:            engine
severity:          low
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          "both, A first (2026-10-27)"
decision_strength: decided
waiting_on:        null
noted:             2026-10-20
closed:            2026-10-27
---
## What

The branch cleanup page that
[`tools/precedent_stale_branches.py`](../tools/precedent_stale_branches.py)
builds carries all its rows as JSON inside the HTML. On 2026-10-20 it was
about 177KB and 1,015 lines, and a republish needed the session to Read
every line first (the Artifact tool refuses one over a version the session
has not read through): seven reads, about 90k tokens. It grows with every
repository it carries.

Proposal: publish the JSON as a data file beside the page (the Artifact
`files` map) and keep the HTML small, so the read a republish needs is
short.

## Why it is asked, not done

The page saves a tick by writing it into its own JSON and saving itself as
a new version (Morgan, 2026-10-13, "Ahhhh great. Go ahead.", decided). With
the data in a separate file, the page would have to save that file
instead, and whether the page runtime can, and whether a republish then
needs that file read through too, is not yet known. If the read-through
applies to the data file as well, the saving is nothing.

## A second option (2026-10-20, a later session)

Measured on the 1,013-line version: every branch is written twice, once as
an HTML row and once in the `branch-data` JSON. If the page's own script
built the rows from the JSON, the saved page would hold each branch once and
the read would be roughly halved, with the self-save left as it is. The cost:
the rows would no longer show without scripts, so a static summary may be
needed for that case.

## 2026-10-27: the cost, and two more options

A session in another repository reported the page at 1,097 lines (197,670
bytes) on 2026-10-27, with the full read measured at about 98,000 tokens.
Since 2026-10-20 the ladder set's
[stale-branch-cleanup](https://github.com/themorgan/precedent-shared-ladder/blob/main/practices/stale-branch-cleanup.md)
rebuilds it whenever the session made, landed or merged a branch, which is
nearly every session, so nearly every closing session pays that read on a
side page. The turn-start note that says to rebuild comes from that set's
[`tools/ladder/branch_page_note.py`](../tools/ladder/branch_page_note.py), which this repo carries as a copy; the
engine's own part is the builder,
[`tools/precedent_stale_branches.py`](../tools/precedent_stale_branches.py).

**Option A, on a keyword (Morgan's proposal, 2026-10-27, as relayed by that
session).** The closing Boildown links the saved page as it stands, one
line, no rebuild. The rebuild and republish run only when Morgan says
"Branch cleanup", the page's name (no command in the vocabulary uses it).
Changes: the practice, its occasion and its note tool in the ladder set,
which declares the phrase, and the "every closing session merges into"
line in [branch-delete-links](../practices/branch-delete-links.md). Cheap
and immediate. The cost: the page goes stale between keywords, and its
"waiting to go live" rows only age, because no session merges them in
unasked.

**Option B, rows in the page's database (the root fix).** Publish the page
once more with the `db` capability and a script that renders from the
database; each repository is one document, its branches and waiting row
inside. A session then writes only the documents for the repositories it
can see, in one `ArtifactData` batch, and never reads or republishes the
HTML. The read-through, the `--merge`, the "older engine erases other
repositories' rows" hazard and the publish-conflict retries all go,
because nothing republishes the page. Ticks and the delete-all button's
"clicked" state move from the page saving itself to database writes, which
the platform keeps across republishes. A refresh then costs a handful of
small writes, so it could stay automatic. The cost: a rewrite of the
builder's output and of the page script, a one-time move of today's rows
into the database, and one write approval in each closing session that
refreshes.

The 2026-10-20 options above are subsumed: B removes the read the data-file
option might not have removed, and makes the halving moot.

**Pick (this session's):** both, in order -- A now, since it stops the cost
at once and is a small change in the ladder set; then B, after which the
refresh can go back to automatic and A's keyword stays as the way to force
one.

**Decided:** Morgan, 2026-10-27: "Both, A first. Reminder this is only for
ladders (so those who don't see ladders shouldn't see the branch cleanup
page or anything about it). Act, Book." (strength: decided).

**A is on the ladder set's staging**
([themorgan/precedent-shared-ladder#130](https://github.com/themorgan/precedent-shared-ladder/pull/130)).
It found the cause of the cost: the 2026-10-20 "rebuild only when asked"
change had reached that set's staging and never its `main`, which every
repository reads. It reaches the other repositories once that set's
staging goes into `main` (Produce), then Update Vendors in each.

**B is built (2026-10-27).** The page's rows live in its own database, one
document a repository
([`tools/precedent_stale_branches.py`](../tools/precedent_stale_branches.py),
"THE ROWS LIVE IN THE PAGE'S DATABASE"). A refresh is an ArtifactData listing,
one `--db-docs` run and one batch of writes for the repositories the session
can see, a few thousand tokens, with no read of the page and no republish.
Morgan's pinned page was moved in place the same day: its last read-through,
one republish of the new page with the `db` capability, and its rows seeded
from the old page, the rows he had ticked left off. That read-through found
the old page's script broken by an unescaped apostrophe, so nothing on it had
run; the harness now parses the page's script. The ladder set's practice
describes the new refresh. The refresh still runs only on "Branch cleanup";
whether it should come back on its own now that it is cheap was put to
Morgan in chat the same day.

## Done when

Morgan picks among A, B, both or neither. On A: the ladder set's practice
and note tool no longer tell a closing session to rebuild, and "Branch
cleanup" is in the vocabulary. On B: the page renders from its database, a
refresh is an `ArtifactData` batch with no page read, and the harness's
branch-page cases pass. On the 2026-10-20 data-file option instead: the page's self-save and `--merge` work with
the data file, a refresh's required read is under about 200 lines, and the
harness's branch-page cases pass.
