---
slug:        computed-numbers-in-scripts
title:       Computed numbers live in scripts; documents embed sync-gated generated blocks
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing a document that cites a computed number"
checked_by:  "tools/doc_sync.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 19
---
## Rule
When a document presents content that a script computes — a summary
table, a cost rollup, a comparison grid — the document region is wrapped in
invisible sentinels:

    <!--gen:NAME-->
    ...generated markdown...
    <!--/gen:NAME-->

the script gains an `--emit NAME` mode that prints exactly that block, and the
(document, block, script) triple is registered with a small sync tool
(`tools/doc_sync.py`). The bare tool run is a **drift gate** — it fails loudly
when the document's block no longer matches the script's output — and runs with
the repo's other pre-commit gates; `--write` regenerates the blocks in place.
Never hand-edit inside a generated block: the numbers live in the script, the
document is a render target.

## Why
Derived numbers quoted in prose silently lag the source that computes
them. Nothing breaks; a human just has to *notice* the staleness — and in one
dependent repo a headline comparison table lagged the scripts behind it until
the repo owner had to ask "did you update the table?". The reminder itself was
the bug: consistency between a computing script and the documents quoting it is
exactly the kind of convention that must become an audit (practice 6), because
it is mechanical to check and embarrassing to miss. The sentinel form matters:
HTML comments render as nothing on hosted markdown, so the plumbing is
invisible to readers, and the block boundaries make regeneration deterministic
(no fuzzy matching against drifting prose).

## Story

## Install
Copy `tools/doc_sync.py`; register pairs in its `PAIRS` list; wrap
the generated regions; give each computing script an `--emit` mode. Wire the
bare run into the same "run before committing" list as the other gates. Start
with whichever document has already bitten you — the one someone had to be
reminded to update.

Two extensions the tool enforces once pairs exist. **The provenance footer:**
every registered document ends with a `**Numbers by:**` footer naming each
script that feeds it (the tool fails on a missing footer or an unnamed
script) — so a reader of the rendered page always knows which code produced
the numbers, without opening the sync tool's registry. **Composition:** an
emitting script may import other computing scripts and re-emit their numbers
in a new arrangement (a per-product sheet drawing on several models); the
sync gate then flags every downstream document when any upstream script
changes — the dependency graph rides the registry for free.

A third extension for documents that absorb concurrent merges. The sync
gate protects only the *generated* regions: a prose section can vanish in a
three-way merge and nothing turns red — and in one dependent repo the owner
asked whether a heavily-merged document had lost a major section (it had
not, but only a manual full-history scan of its section headers could prove
it). Where a document accumulates sections across concurrent branches, keep
a **required-sections list** beside the computing script's self-assertions —
a check that fails when a listed header is absent from the document. A
deliberate rename or removal updates the list in the same change; an
accidental merge-loss fails the build. The retroactive form of the same
check — every section header any commit ever added, compared against the
current document — answers "did we already lose something?" once, when the
suspicion first arises; the list encodes it forward.
