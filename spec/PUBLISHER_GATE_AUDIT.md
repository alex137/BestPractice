---
title:         Which checks bind a practice source set
kind:          record
status:        closed
opened:        2026-09-22
closed:        2026-09-22
superseded_by: null
supersedes:    []
audience:      session
summary:       "All 44 checks that a practice source set skips for want of a local practice file, measured one at a time with binds_publishers forced on: which 13 now carry the flag, which 26 cannot function there, and why the 5 that produce findings were left off."
---

# Which checks bind a practice source set

[`precedent_check.py`](../tools/precedent_check.py) runs a check only where `practices/<slug>.md` exists in
the repo being checked. That gate is correct for a consumer — a finding for a
practice it does not have is one it can never act on — and **exactly wrong for
a practice SOURCE set**, whose `practices/` holds its own catalogue only.
`binds_publishers=True` removes the gate for a check whose subject really is
the published practice tree. Three checks carried it before today.

This is the measurement that decided which others get it.

## What was measured

Every one of the **44 checks** that a source set skips with *"no
`practices/<slug>.md` in this repo"* was run individually with
`binds_publishers` forced on in memory and `--full-sweep`, in
`precedent-shared-writing` first and then in the other two reachable shared
sets. The fourth source, the individual set, was **not measured** — its clone
was stale and unpushable at the time (17 local commits not on `origin`), so
anything read there would describe an old catalogue.

All four sources skip the same 44, for the same one cause.

**Functioning is necessary and not sufficient.** The flag's own docstring says
to set it *"only where the check's subject really is the published practice
tree, and only where the check is known to FUNCTION in a source set."* Twenty-four
of the 44 function. Thirteen of those have the published tree as their subject.

## Flagged (13)

Each of these reads a practice file, a practice filename, or the source
declaration itself — the things a source set publishes and a consumer
receives.

| Check | What makes it a publisher's rule |
|---|---|
| [cite-the-incident](../practices/cite-the-incident.md) | A practice file whose Rule changed must carry a Story. A source set is the only place a practice is written, so it is the only place this can fire. |
| [source-naming](../practices/source-naming.md) | Its whole subject is being a declared source set. The gate was backwards for this one from the day it was written. |
| [decision-strength](../practices/decision-strength.md) | Reads `strength:` out of practice files. |
| [acronyms-glossary](../practices/acronyms-glossary.md) | An acronym left unexpanded in a practice file arrives unexpanded in every consumer, next to a [`GLOSSARY.md`](../GLOSSARY.md) none of them can see. |
| [doc-references-are-links](../practices/doc-references-are-links.md) | A tilde span renders as strikethrough wherever the practice lands. |
| [heading-outline](../practices/heading-outline.md) | A practice file has a fixed heading structure; a skipped level ships malformed. |
| [label-describes-content](../practices/label-describes-content.md) | A practice file's own headings and bold lead-ins. |
| [docs-are-current-state](../practices/docs-are-current-state.md) | An `(added <date>)` tag annotated into a practice travels into repos whose history does not contain that date. |
| [index-remembers-past](../practices/index-remembers-past.md) | Inline lineage travels with the practice; the index that should hold it does not. |
| [deliverables-look-like-output](../practices/deliverables-look-like-output.md) | Process residue written into a practice ships with it. |
| [no-version-suffix](../practices/no-version-suffix.md) | A practice added under a versioned name is published under it. |
| [filename-separator](../practices/filename-separator.md) | `practices/` is a directory of one kind of file, and its names are published. |
| [technical-describes-people](../practices/technical-describes-people.md) | A practice filename is a published path. |

**Twelve of the thirteen pass in all three measured sets. One finds something
real**, and whoever next runs the checks in the repo-maintenance set will see
it rather than be surprised by it:

```
VIOLATION  filename-separator
    .: 1 file(s) use "-" and 7 use "_" for the same kind (*.md) in one
       directory -- pick one, or exempt the group in precedent.json with
       the reason each name was determined elsewhere
```

A date in one root-level filename against the `_` convention of the seven
beside it. The remedy is the one the finding names: rename it, or record the
exemption with its reason. Not fixed here — it is that repo's file, and this
change is the engine's.

One clean skip: `acronyms-glossary` declines in the working-style set, whose
own markdown is too small a corpus to tell a shouted word from an initialism.
A decline is the designed behaviour, not a failure.

## Functions, but not flagged (6)

These run cleanly in a source set and pass. They are still gated, because what
they inspect is the repo's own machinery rather than anything it publishes —
and a source set does not own most of that machinery, it vendors it.

| Check | Subject |
|---|---|
| [orientation-map](../practices/orientation-map.md) | [`MAP.md`](../MAP.md) exists at the root. A property of the repo, not of its catalogue. |
| [open-item-disposition](../practices/open-item-disposition.md) | `**Disposition:` lines in the set's own todo files, which no consumer receives. |
| [todo-migrate-available-but-unused](../practices/todo-migrate-available-but-unused.md) | Whether this repo has run the todo migration. Repo state. |
| [generated-edit-goes-upstream](../practices/generated-edit-goes-upstream.md) | `do not hand-edit` headers on vendored files. An engine property. |
| [workflow-file-outside-vendoring](../practices/workflow-file-outside-vendoring.md) | Workflow files against the vendoring manifest. An engine property. |
| [timestamps-carry-offset](../practices/timestamps-carry-offset.md) | Bare `date.today()` in tracked Python — which in a source set is overwhelmingly **vendored engine code the set cannot fix**. It passes today by luck of what upstream ships; flagging it would hand a source set a finding whose only honest remedy is upstream. |

## Produces a finding, and still not flagged (5)

The tempting four. Each of these reports something when the flag is forced on,
which is why they looked like the case for flagging — and reading the findings
is what settled it the other way.

**[code-cites-practice](../practices/code-cites-practice.md) — a false
positive, and a real bug.** It reported `create_word_doc.py` (in that set) citing
`timestamps-carry-offset`, *"which is not a real practice slug."* It is a real
slug; it lives in this repo. The check validates slugs against the LOCAL
`practices/` directory, which in a source set holds twenty files and not the
catalogue. Flagging it would have turned a correct citation into a blocking
violation in three repos at once. Filed as
[todo/todo-2026-09-22-code-cites-practice-validates-against-the-wrong-catalogue.md](../todo/todo-2026-09-22-code-cites-practice-validates-against-the-wrong-catalogue.md);
it is flaggable once it resolves slugs the way a session does.

The other three all report against the source set's **[`AGENTS.md`](../AGENTS.md)**, not
against anything it publishes:

| Check | What it reported |
|---|---|
| [quick-index](../practices/quick-index.md) | its `AGENTS.md` carries no "looking for X → go to Y" table |
| [two-check-levels](../practices/two-check-levels.md) | its `AGENTS.md` names no fixed light-check / deep-check pair |
| [environment-gotchas](../practices/environment-gotchas.md) | its `AGENTS.md` has no "do NOT rediscover these" section |

Those are plausibly worth fixing in each set. They are not this flag's
business: the flag says *the published practice tree*, and a source set's
instructions file is read by sessions working in that set, by nobody
downstream. Widening the flag to mean "any rule a source set ought to follow"
would make it the second gate rather than the exception to the first, and
there would then be no principle left deciding the remaining 26.

**[routing-audit](../practices/routing-audit.md)** reported [`tools/routing_audit.py`](../tools/routing_audit.py)
missing. That is a tool this repo authors and a source set has no reason to
carry. Subject is the tool, not the tree.

## Cannot function there (20)

Recorded so the next session does not re-measure them. They skip for a stated
second reason even with the gate removed, and no flag changes that.

**Missing the tool the check drives (7)** — `computed-numbers-in-scripts`,
`docs-track-models`, `document-status-header` and `speculation-is-marked` need
[`tools/doc_lifecycle.py`](../tools/doc_lifecycle.py); `practice-export-loop` and `scrub-gate` need
[`tools/practice_audit.py`](../tools/practice_audit.py); `scripts-assert-properties` needs
[`tools/model_audit.py`](../tools/model_audit.py). None is vendored into a source set.

**Nothing of that kind exists there (13)** — `ci-commits-carry-identity`,
`decommission-deletes-files`, `engine-plus-host-shims`, `github-api-budget`,
`github-setup-disclosed`, `headline-capitalization`,
`migration-scrubs-vocabulary`, `parallel-artifact-ledger`,
`rename-updates-links`, `search-by-purpose`, `session-bootstrap`,
`session-load-budget`, and `layered-practice-packs` (advisory only, and its
subject is a consumer's pack layering).

## What this does not settle

**Whether the 26 left behind should be reached some other way.** The
publisher flag is one exception to one gate. A source set that ought to carry
a quick index, or a declared check pair, or a gotchas pointer, needs a
mechanism that says so — not a flag whose name means something else. Nobody
has proposed one; this record exists partly so the next person to want one
finds the evidence already gathered.

**Whether the passing twelve stay passing.** They pass against the three
shared sets as they stand on 2026-09-22. A source set that grows a document
with a skipped heading level will find out, which is the point.
