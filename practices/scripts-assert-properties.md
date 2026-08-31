---
slug:        scripts-assert-properties
title:       Scripts assert their own properties, and the figures their source documents recite
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing a script whose numbers a document will cite"
index_clause: "scripts assert their own properties and their cited anchors"
checked_by:  "tools/model_audit.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 30
---
## Rule
A script that computes numbers other work depends on carries two
kinds of executable assertion, and an audit (`tools/model_audit.py`) runs them
with the repo's other gates:

- **`self_check()` — property assertions on its own outputs.** Not "is this
  value right" but "does this output satisfy the properties it must satisfy":
  an invariance, a monotonicity, a conservation, an ordering, a ratio held by
  construction. Returns a list of failure descriptions; empty means pass.
- **`ANCHORS` / `check_anchors()` — figures recited in an authoritative source
  document** that the script must reproduce. Each anchor names the document and
  section that recites it. Compare as **band overlap**, not equality, when
  either side is an estimate.

Two rules make the difference between this working and being theatre.
**Assert properties, not values** — a value comparison cannot catch a correct
input transformed by a wrong law. And **never refit an anchor to silence it**:
a failing anchor means a script and a document of record disagree, which is
always a human's decision, and the resolution runs in both directions.

Scope it. Instrument the scripts that **consume or re-derive a quantity another
script or an authoritative document owns** — that is where this failure class
lives. Scripts that own their own numbers end to end need nothing. Keep the
instrumented list explicit so the audit can warn when a listed script has no
assertions.

## Why
The obvious diagnosis for a wrong computed number is a stale copy, and the
obvious fix is a shared constants module.

It was prose everywhere and executable nowhere, and **prose does not fail a
build**.

Generalise that: **the most carefully reasoned documents in a repository are
often the ones checked by nothing.** They are written slowly, by whoever
actually reasoned the thing through, and then they sit — while fast-moving
derived artifacts get all the tooling. Driving everything from the scripts is
the natural instinct and it is backwards here; it would have propagated the
error faster. The document was the more reliable artifact and the more neglected
one at the same time.

## Story
In the incident that produced this practice, both were wrong.

A script published results that were out by a third at one input and by more
than a factor of three at another; work sized from them would have been badly
undersized. The constant it started from was **correct, correctly labelled, and
identical in the two sibling scripts that also used it** — one of which even
stated the governing property in its own docstring. The script cited its source
correctly. A shared constants module would have handed it exactly the right
number and the defect would have survived untouched, because the defect was in
the **transformation applied after import**: a scaling law applied to a quantity
whose defining property is that it does not scale.

That property was written down — in two sibling scripts' docstrings, in the
owning script's printed output, and in the figures recited by the
authoritative document.

The sharpest part is where the correct number actually lived. **The
authoritative document was right and the script was wrong.** The document
recited the correct figure for exactly the case the script got wrong — and the
sync gate of practice 19 faithfully published the script's number into the
derived document, because it guards *document agrees with script* and cannot
know the script is wrong. Every artifact was internally consistent; the only
disagreement in the repo was with the one document nothing compared against.

Two further returns showed up immediately on installing this. First, an anchor
failed in a script written **by the same session that had just been burned by
this exact class of error and was actively watching for it** — care did not
prevent the repeat, the executable check did, on its first run. Second, anchors
surface **unstated assumptions in the source documents**: one recited figure
turned out to hold only under a qualitative condition the document never
quantified, and the unconditional figure — the one anything must actually be
sized to — was materially different. Neither of those is findable by reading.

## Install
Add `tools/model_audit.py`; list the scripts to instrument in its
`INSTRUMENTED`. In each, add `self_check()` returning failure strings, and
`ANCHORS` as `(label, lo, hi, callable -> (lo, hi))` with `check_anchors()`
comparing by overlap. Label every anchor with the document and section it comes
from. Wire the bare run into the same pre-commit list as the other gates.

Start where a quantity crosses a boundary: the first script that takes a number
it did not derive. Write the assertion as the sentence you would use to explain
the quantity to someone — *"these must be equal by construction"*, *"this can
only decrease"* — because that sentence is the property, and the property is
what a wrong transformation violates.

When an anchor fails, record which way it resolved. In the origin round of three
failures, one was the script's error, one an unstated assumption in the
document, and one a superseded input; all three were written down and none were
fitted away. That record is what keeps the mechanism honest — an anchor quietly
widened to pass is worse than no anchor, because it now certifies the thing it
stopped checking.

**A detector for a specific sub-class: solved outputs that repeat across
cases.** When a script solves a quantity per case — per configuration, per
variant, per row of a comparison — an identical value appearing across cases
with different inputs is a defect signal: a constant is hiding where a
per-case solution belongs. The origin instance was exactly this shape: one
variant family's supposedly-solved parameter was a single hand-copied number
across every case, and the number turned out to be a figure borrowed from an
*unrelated* constraint in a predecessor analysis — recognizable by value, wrong
in role — which a user caught by asking why cases with different inputs shared
an output. The check is mechanical and cheap: collect each solved output across
cases; a value shared by two cases with different inputs must be explained by a
**named shared constraint** the solver reports as its binding limit; an
unexplained repeat fails. This also catches the softer form, where a shared
*class default* (a duty factor, a lapse, a rating) silently reaches a case
whose class it does not fit — the same session found one of those the same day,
and the tell was again a column identical across rows that should have
differed.

**Related.** Practice 19 guards *document agrees with script*; this one guards
*script agrees with reality and with the document of record* — the edge one
level up, and the one that bites when the script is the wrong artifact.
Practice 6 (conventions become audits) is the general form. Practice 20
(mistakes become rules) produced it, including the correction of its own first
root-cause analysis, which named the stale-copy diagnosis above and had to be
retracted when a one-line check disproved it. Practice 29 (a variant re-derives
what it inherits) is the drafting-time counterpart of the repeat detector
above.
