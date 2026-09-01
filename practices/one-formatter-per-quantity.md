---
slug:        one-formatter-per-quantity
title:       Every quantity kind prints through one formatter
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "printing a numeric quantity that will be compared across rows"
gates:       []
index_clause: "one formatter per quantity kind, declared in one module"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 51
source_rule_unlabeled: true
---
## Rule
A reader comparing two table cells must never have to normalize precision
in their head. **Declare one formatter per quantity kind** — tonnage,
volume, money-rate, speed, distance, whatever the domain's comparable
quantities are — **in a single module, and route every emitter that
prints the kind through it.** Never an inline format string: an inline
`f"{x:.1f} t"` is a second, silently divergent copy of the kind's
precision policy, and the divergence prints as "2 t" in one cell and
"2.0 t" in the next.

The formatter object carries the kind's **whole** policy: decimal places,
any threshold above which values print as thousands-separated integers,
approximation marking, unit affixes.

## Detail
**The underlying rule — representation is a property of the comparison
set, not of the individual value.** Every recurrence of this defect class
has the same shape: the format was computed from one value at a time (a
per-value threshold, per-value significant figures, two "kinds" that in
fact share columns), and any function from a single value to a string can
break set-consistency the moment the set spans it. Choose the
representation once, from the whole set of values that will be compared
together, and apply it to every member. Three policy rules with teeth:

- **Pick precision from the estimate's own noise.** Tenths the model
  cannot resolve are false precision; a kind whose values are rough
  estimates prints coarse everywhere, not just where someone remembered.
- **Check thresholds against the comparison pairs.** A threshold is safe
  only if no two values a reader will compare side by side fall on
  opposite sides of it — a policy that prints one cell as an integer and
  its row-mate with a decimal has recreated the original defect inside
  the formatter.
- **Currency uses the money convention: one fixed decimal count across
  the compared set.** Significant figures are honest about noise but
  print $16 beside $1.4 beside $0.030 — three shapes for one kind, and
  money is the kind readers subconsciously column-align. Fix the decimal
  count for the whole set (verify it still separates every pair actually
  compared; widen it if not), and accept the mild over-precision on the
  large values as the cost of alignment.

## Why

## Story
**Origin.** A competitive-comparison table printed an incumbent's
capacity as "2 t" beside the fleet's own "2.0 t" in the same row — the
principal flagged it as proof the table was not being read the way a
reader would. The first fix — two ad-hoc helpers inside that one table's
emitter — immediately straddled its own threshold: integers at 100 put
"110" beside "97.8" in the same row, the same defect in new clothes. A
third pass moved the money kind to per-value significant figures — honest
about noise, and still wrong: $16, $1.4, and $0.030 are three shapes of
one kind. Only then did the class close, with the set-level rule above:
every fix until it had computed the format from a single value, and the
requirement was never a property of single values.

## Install
**Engine.** `tools/table_fmt.py` (`Qty`): the mechanism — threshold
precision, separators, approximation and affixes — as a tiny class. A
host repo's shim declares its kinds once ([engine-plus-host-shims](engine-plus-host-shims.md)) and its emitters
import the shim. Adopting emitters must reproduce byte-identical output
where the policy is unchanged — the generated-block drift gate
([computed-numbers-in-scripts](computed-numbers-in-scripts.md)) is the proof.

**The formatter↔renderer seam is checked, not remembered.** The sortable
render parses these printed strings back to numbers for sorting,
frontier ranking, and decimal alignment — so the formatter's output
grammar and the renderer's parse grammar are one contract with two
implementations, and nothing about a new notation looks broken until a
table silently mis-sorts it. The engine therefore ships `parse_key()`
(the Python mirror of the renderer's numeric-key grammar; the two are
extended together) and `roundtrip_check()`: every registered kind
formats sample values and the parse must recover the printed value —
the expectation derived from the kind's own declared affixes, so it is
independent of the parser — plus canned grammar pins for the forms that
drift silently (the unit-vs-money "M", the bare decimal). A host shim
exposes this as `self_check()` wired into the repo's audit runner, so a
notation the tables would mis-sort fails at commit time, not in the
browser.

**Related.** [tabular-shared-renderer](tabular-shared-renderer.md) (the render layer these cells land in);
[docs-track-models](docs-track-models.md) (transformations live in code — this is its formatting
corner); [engine-plus-host-shims](engine-plus-host-shims.md) (how the engine crosses the repo boundary).
