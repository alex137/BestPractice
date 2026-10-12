---
slug:              todo-2026-10-12-rendered-docs-are-not-rebuilt-automatically
kind:              manual
domain:            mechanism
severity:          null
status:            done
disposition:       null
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-12
closed:            2026-10-12
---
## What

- [x] **[spec/PREFORK_AUDIT.html](../spec/PREFORK_AUDIT.html) keeps going stale on `main`, and every merge into `main` fails until someone rebuilds it.**

It has needed a hand rebuild at least three times (160fb3bc on 2026-10-04,
a85fec09 and 132b3fd5 on 2026-10-12). Each time,
`check_rendered_docs_are_current` in
[tools/verify_harness.py](../tools/verify_harness.py) fails the full check
for whatever pull request happens to be merging, and that pull request
has nothing to do with the render.

**Cause.** The commit backstop,
[tools/precedent_regenerate.py](../tools/precedent_regenerate.py), rebuilds
only what [tools/generated_files.json](../tools/generated_files.json)
lists, and the render is not listed. So a change to
[tools/doc_html.py](../tools/doc_html.py)'s page template or to the
render's source never rebuilds it. The render can't simply be listed
either: the registry's label check (`_generated_label` in
[tools/precedent_check.py](../tools/precedent_check.py)) reads labels only
from Markdown and JSON, and has no label for HTML.

**Proposed fix.**
1. [tools/doc_html.py](../tools/doc_html.py) writes a `<meta name="generated_by">` label naming the renderer into every render.
2. `_generated_label` (and `_label` in the commit backstop) reads that label from an `.html` file.
3. One registry entry per render in `DOCS`, with inputs = its source and the renderer, regenerate = the renderer run bare.

**Why this is waiting on a decision.** The renderer is vendored, so step 1
labels every render in every consumer. One consumer keeps many renders
with a publisher session of its own. Its check would then demand a
registry entry for each render, and its commit backstop would start
rebuilding them. That needs either a consumer-side opt-in or a change to
how that consumer publishes, which is a call for the people who run it.
A cheaper alternative inside BestPractice alone: have
`check_rendered_docs_are_current` rebuild a stale render and say so,
instead of failing the merge. That treats the symptom, though, not the
cause.

## How It Closes

The render is rebuilt automatically whenever its source or the renderer
changes, and a merge into `main` no longer fails on it; or the person
picks the alternative or drops the item.

## Notes

2026-10-12: closed on its condition, with neither the proposed fix nor the
alternative. Alex chose the full fix and asked for one that would not
force so much work next time. The proposal above needed a second list
(a registry entry per render, plus a label in every render) for pages
the renderer already lists, and that second list was what rippled into
every consumer. Instead, the commit backstop
([tools/precedent_regenerate.py](../tools/precedent_regenerate.py)) now
re-renders from the renderer's own `--list`, the way it already refreshes
doc_sync's generated blocks from their own list: a page whose source or
the renderer is in a commit is re-rendered into that commit. A consumer
whose renderer lists nothing (one with no host file) sees no change.
[tools/generated_files.json](../tools/generated_files.json)'s notes now
state the rule for the next generated kind: the backstop reads the
tool's own list and never asks for a second one.

2026-10-12, later: that was half the cause. The full check then failed on
the same page with the backstop in place: two clones spell the
repository's address differently (an attached clone's origin is
lowercased), the renderer built its links from the origin as spelled, and
each machine's rebuild made the other's check fail. That explains the
hand rebuilds that kept flipping (132b3fd5, then d7829a6b).
[tools/doc_html.py](../tools/doc_html.py) now lowercases the GitHub part
of its link base, so every machine renders the same page.
