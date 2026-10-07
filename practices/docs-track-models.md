---
slug:        docs-track-models
title:       Documents track their models, and every transformation lives in code
tier:        on-demand
severity:    default
applies_to:  ["**/*.md"]
applies_to_why: "Set at phase 1 from the Install text, which named a path unambiguously. Decided: phase 1."
occasion:    "a document presents a script-derived figure"
gates:       []
index_clause: "every script-derived figure sits inside a generated block"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 33
---
## Rule
Extending [computed-numbers-in-scripts](computed-numbers-in-scripts.md) from *tables* to **every** figure a script
computes:

1. **A script-derived figure appears in a document only inside a generated
   block.** Including figures embedded in running prose — those are the ones
   the sync gate cannot see, and therefore the ones that rot.
2. **Never restate a generated number in the prose around its block.** Point at
   the table instead. A restatement is a second copy with no gate on it. If a
   figure genuinely must appear in a sentence, put the sentence inside the
   block.
3. **Every transformation belongs in the emitter.** Unit conversions, rounding,
   banding, audience-facing phrasing, redaction for external copies — all code.
   A number converted by hand is a number nobody can regenerate, and a rounding
   applied by hand is a rounding nobody can audit.

When a script changes, every dependent document changes with it, in the same
commit, by regeneration rather than by editing.

4. **Published pages: only a render reaches a link.** A page published for
   people to read is a copy of what the renderer produced from a registered
   document, never a page written by hand, however early or rough the
   draft. A page made outside the repository is outside every check above. A page one
   of the engine's own generators writes, published unedited within the
   hour, is a render too: the branch-cleanup page is one.

## Detail

## Why
Hand-applied transformations hide the same way. A metric figure typed again in
feet is two numbers that must be maintained together and will not be; a range
"rounded for prose" is an editorial decision with no record of which direction
it moved. Both look like writing and behave like un-versioned code.

The scope limit matters: **this applies to documents not yet issued.** An
artifact already sent to someone is a record of what they received and must not
be silently regenerated — fix the source, mint a fresh copy, and let the
distribution record show both.

## Story
A sync gate only guards what it can see. In the incident that produced
this, a defective script published wrong figures into several documents; the
generated tables were corrected automatically the moment the script was fixed,
and the **hand-written prose statements in the same documents stayed wrong** —
found later only by a deliberate contamination sweep. The gate had worked
perfectly on everything it was pointed at, which is precisely why the gaps were
invisible.

Rule 4 has the same shape one level out (2026-10-05, a consumer). A deck's
review page was built by hand in a scratch folder, with its figures typed in,
and published straight to a link so its contents could be agreed before the
real build. Every check on script-derived figures reads files in the
repository, so none of them ever saw that page. A model then changed one of
the figures and the page kept the old one for nine days, until the deck was
rebuilt from the models and the two disagreed.

## Install
**Rule 4 is a hook.** `hooks/artifact-publish-gate.sh` runs
[tools/artifact_publish_gate.py](../tools/artifact_publish_gate.py) before
every Artifact publish and refuses a page that is not byte-identical to the
on-disk render of a registered document, or whose render is older than its
source. The registry is the renderer's `DOCS` and `COMPOSITE_RENDERS`
(`tools/doc_html.py`, or the host shim named in
`tools/artifact_publish_gate_host.json`). A page that is not a deliverable is
registered and rendered like any other; that cost is the point.

**The engine's generators pass the same way** (2026-10-07). A tool listed in
the gate's `GENERATORS` notes the sha256 of every page it writes;
[tools/precedent_stale_branches.py](../tools/precedent_stale_branches.py)
`--html` is the one listed. Its page has no model behind it, so nothing can
drift, and the gate's question -- is this exactly what the tool produced,
recently? -- is the one it asks of a render. A consuming repository's session
was told by one rule to publish that page and refused by this one, and fell
back to pasting links into chat.

**Enforced, not merely stated.** Rule 2 is mechanically checkable and now is:
a script declares the figures it owns via `owned_figures()`, returning them in
the **exact rendered forms it produces** — value and unit, formatted as the
emitter formats them — and the sync tool greps every document *wired to that
script* for those strings outside its generated blocks. Three scoping choices
keep it usable rather than noisy: only wired documents are scanned, only
declared figures are searched, and matching requires a **unit boundary** so
`30 m` never matches `30 m/s`. That last one is not hypothetical — it was the
first thing the check got wrong, firing on two speeds on its first run, and it
is the reason a naive scan for "numbers a script produced" is worthless. A
deliberate restatement is marked `<!--owned-ok-->` on the line. Scripts that
declare nothing are not checked; instrumentation is opt-in, per script.

When wiring a document: wrap every script-derived figure, give the
emitter an audience-appropriate form (the same numbers may want a different
table for an internal reader and an external one — that is two emitters, not
two hand-edits), and put the provenance footer at the foot of the document so a
reader knows which code produced what. Then **sweep the prose** for figures the
scripts own and either wrap them or replace them with a pointer; a short regex
sweep over the owned quantities finds these quickly and is worth re-running
whenever a script's outputs change shape.

A companion audit closes the loop the other way: **the registry that wires
documents to scripts is itself verified** (an unregistered generated block is
one nothing checks, and its numbers rot silently while every gate reports
green), and a document may **opt in** — placing a marker alone on a line — to a
stricter rule that *every* quantity in it be generated, cited to an external
source, or explicitly marked an estimate. Measure before making that a
repo-wide gate: in the origin repo ≈91% of quantity tokens were unexplained, so
the strict rule is per-document opt-in, and a report mode sizes the backlog
without blocking anything. Two false-positive traps are worth inheriting: match
declared figures with a **unit boundary** (else "30 m" matches "30 m/s"), and
require the opt-in marker to be **alone on its line** (else a document that
merely mentions the marker opts itself in and fails on its own examples).

Where a document needs figures from several scripts, let the emitter **import**
the other scripts rather than restating their numbers, so each figure keeps
exactly one owner ([computed-numbers-in-scripts](computed-numbers-in-scripts.md)'s composition extension, and [scripts-assert-properties](scripts-assert-properties.md)'s
one-owner rule applied to documents).

**Related.** [computed-numbers-in-scripts](computed-numbers-in-scripts.md) (generated blocks) is the mechanism; this is its
scope. [scripts-assert-properties](scripts-assert-properties.md) (scripts assert their properties and their sources' figures)
guards the layer below — that the script is right before its numbers are
published everywhere automatically.
