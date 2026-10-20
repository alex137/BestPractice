---
slug:              todo-2026-10-20-branch-page-data-in-a-file
kind:              manual
domain:            engine
severity:          low
status:            open
disposition:       ask
remind_on:         null
blocked_on:        "Morgan's call: it changes how the page saves ticks into itself, which he chose on 2026-10-13"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-20
closed:            null
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

## Done when

Morgan says yes or no. On yes: the page's self-save and `--merge` work with
the data file, a refresh's required read is under about 200 lines, and the
harness's branch-page cases pass.
