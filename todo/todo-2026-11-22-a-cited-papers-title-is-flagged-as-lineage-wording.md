---
slug:              todo-2026-11-22-a-cited-papers-title-is-flagged-as-lineage-wording
kind:              manual
domain:            engine
severity:          low
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-11-22
closed:            null
---
## What

- [ ] **The check that keeps "what replaced what" out of documents flags a cited paper's own title.** Reported 2026-11-22 from a project: a generated list of sources cited a published paper whose title contains the words "A Successor to", as the text of a link, and the `index-remembers-past` check refused the document for "inline lineage language". The project's stopgap was to cite a short title. (needs: session -- out of scope for the research session that filed it, which was told to change no check)

**Why it happens.** The check in [tools/precedent_check.py](../tools/precedent_check.py) (`_index_remembers_past`) runs its pattern over each raw line of a changed document. It does not set aside the text of a link, a quoted title or a generated block. Confirmed by running the pattern on a line holding that title as link text: it matches.

**The fix, at the cause** ([upstream-fix](../practices/upstream-fix.md)): before matching, drop link text and quoted spans from the line, so a title somebody else wrote is never read as this document describing its own history. A sentence of the document's own that says one file took over from another is still caught. A test plants both cases.

**The cost of leaving it.** Any document that cites a work with those words in its title is refused, and the way through is to misquote the title.

## How It Closes

`status` becomes `done` when the check passes a document citing such a title as link text or in quotation marks, still refuses the same words in the document's own prose, and both cases are in its test.
