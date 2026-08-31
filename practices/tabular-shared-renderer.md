---
slug:        tabular-shared-renderer
title:       Tabular documents ship a sortable render from one shared renderer
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "publishing a document with a multi-column sortable table"
index_clause: "ship a sortable render from the one shared renderer"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 46
---
## Rule
When a document's tables have multiple columns a reader might want
to sort — a trade study, a parameter sweep, a comparison matrix — the
markdown alone is not the finished product. Ship an HTML render delivering
the behavior contract below. The source document remains the source of
record (with its generated tables kept live by the doc↔model sync of
practice 33); the render is a committed build product, rebuilt after any
edit.

**The load-bearing half is singularity.** All table behavior — CSS, JS, sort
semantics, numeric-aware sort keys — lives in **one** shared renderer with a
registry of the documents it renders ([tools/doc_html.py](tools/doc_html.py)
is the reference implementation). A functionality change is made there and
only there, and the no-argument invocation rebuilds every registered render,
so the change manifests in every table at once. The test for a new
capability follows: it must manifest on every registered render **from the
engine alone** — a host or per-document declaration may refine it, never
gate it, or the "change once, upgrade everywhere" property is silently lost
for every table that lacks the declaration. Per-document build scripts may
survive as documented entry points, but as thin wrappers importing the
shared `render()` — never as forks of the CSS/JS.

## Why
The failure this kills is the same one practice 33 kills for numbers: N
copied renderers drift independently, and the oldest copy is the one a
reader eventually trusts.

**Why sortable matters enough to be a rule.** A wide cross-product table
(say, 4 loads × 3 price points × 9 altitudes) is written in one canonical
order, but every reader arrives with a different question — cheapest rows
first, group by one factor, find the regime boundary in another. Static
markdown forces the writer to guess one question and answer only it; a
sortable render answers all of them without another build. The cheap test:
if you catch yourself emitting the same table twice in different orders, the
document wanted this practice.

## Story

## Install
**The behavior contract.** This is what the reference implementation
([tools/doc_html.py](tools/doc_html.py)) delivers on every table, and what
any reimplementation on another stack must match — it is the spec a reader
of this practice is entitled to assume when a repo says "practice 46
render":

1. **Multi-column sort** — click a header to sort; shift-click (or a
   Multi-sort toggle) adds secondary keys; clicking a key again reverses
   it; marks on the headers show direction and key order.
2. **Numeric-aware sort keys** — cells sort numerically through the
   notation documents actually use: approximation marks (≈/≤/≥), any
   Unicode currency symbol, thousands separators, leading zeros, bare
   decimals, magnitude suffixes (k, M — recognized on currency amounts
   only, since a bare "M" is usually a unit), trailing units; empty and
   em-dash cells sort last. The same key drives the frontier axis
   pull-down (item 8), so a column ranks exactly as it sorts.
3. **A filter dropdown on every column** — no column is left without
   one. The panel offers what the column supports: a multi-select
   checkbox list of distinct values where the set is usefully small
   (2–60; any checked subset keeps its rows, none checked = "All", the
   default), plus on **value columns** a comparator — pick </≤/=/≥/>
   and type a threshold in the displayed units (cells that don't parse
   never pass) — and on text columns too varied to enumerate a
   contains match. A column's constraints AND together, the button
   shows the active selection, and filters compose with each other and
   with sorts. Multi-select is the point — comparing two named
   alternatives side by side is the most common filtering ask a
   comparison table gets; the comparator serves the "under $X /
   over Y t" ask value columns get. A value column is one whose cells
   *lead* with a number (the practice-46 item-12 test): "Rotax 916"
   contains a digit but is a name. On a text column that is a frontier
   ordinal axis (item 8), the dropdown's value rows list in the axis's
   current best→worst order and each carries a ⠿ grip that drags the
   row to re-rank — the same order the frontier picker edits, editable
   from whichever panel the reader has open; the checkbox still
   filters, only the grip drags.
4. **Active columns pin in place and stay visible** — sorted and filtered
   columns stick at the viewport's left edge as the table scrolls past
   them, without being moved from their positions; the header row stays on
   screen under vertical scroll. The reader's working columns never leave
   the viewport, and nothing rearranges itself. (Revised from an
   automatic move-to-left-edge behavior, which field use found confusing —
   the table reorganizing on every sort click; movement is the reader's
   act, not a side effect.)
5. **Draggable column order** — drag a header to move a column; dragging
   is the only way columns move. Implement every drag (this and the
   ordinal value lists of item 8) with **pointer events, never native
   HTML5 drag-and-drop**: hosted artifact viewers run renders in
   sandboxed frames where native DnD never fires (verified 2026-08-28),
   and pointer events also work on touch. Two traps: put the
   move/up listeners on the **document**, and do **not** pointer-capture
   the dragged element — re-inserting it in the DOM (the reorder itself)
   implicitly releases capture and kills the drag after its first swap.
   Gate the header drag behind a small movement threshold so plain
   clicks still sort.
6. **One Reset** — clears sorts AND filters and restores the original row
   and column order.
7. **Live row count** — "N of M rows" tracks filtering.
7b. **Alternate-value views (optional)** — a cell may carry one
   `<span data-view="NAME">` per view of the same quantity (e.g. two
   pricing bases); the first view named is the default, and each
   further view gets a checkbox that swaps every such cell at once,
   re-sorting on the visible values (filters clear, since their value
   sets changed). Sorting, filtering, and the row count always read
   the ACTIVE view's text, never the concatenation.
8. **Frontier axis pull-down** — where a Frontier column exists
   (practice 47), the render opens showing frontier rows only, and the
   control is an axis pull-down that works on any such table with no
   per-document wiring: the printed ✓/— marks (the model's own
   computation, per practice 47) are the default view; the picker
   offers **every** other column as an axis and recomputes the marks
   client-side on a custom pick. A numeric column takes a reader-set
   better-direction (↓/↑); a **text column ranks as an ordinal axis
   by its value list, which the reader drags into best→worst order**
   (default: the column's sorted order; each value row carries a ⠿
   grip icon marking the drag affordance) — only a text column with too
   many distinct values to order is listed as not rankable. An "All
   rows" entry clears the filter. A generating model may curate the
   picker with an invisible frontier spec beside its table — fixed
   directions for the columns it names, input tags (informational,
   still selectable), the default axes, a partition column judged
   separately (format in the renderer's docstring) — but the spec
   refines the pull-down, never gates it: unnamed columns are still
   offered.
9. **Header definitions round-trip** — a header links to its definition
   note and shows it as a mouse-over tooltip; the note's return link lands
   back on the exact header cell it defines, not merely the table's
   section.
10. **The render is the versioned product** — it carries its build
    timestamp in the page header; the source carries none (version control
    is the history).
11. **Page mechanics** — source-file includes are expanded; relative repo
    links are rewritten to the hosted view; wide tables scroll inside
    their own container rather than the page.
12. **Decimal-aligned numeric columns** — in a column whose cells lead
    with a number (approximation marks, ×, or a currency symbol may
    precede it), each cell is padded so the number's integer end — and
    hence its decimal point — sits at one x-position down the column.
    The prefix is pixel-measured (markup-safe), so bold text, links,
    and proportional-width symbols align exactly, and trailing
    annotations don't disturb the line-up; a bare decimal (".45") has
    an empty integer part, so its point lands on the same line as
    "0.45"'s. Columns whose digits appear only inside text (part
    codes, composite cells) are left alone.

**Singularity crosses the repo boundary.** In a dependent repo, the
vendored copy of the renderer **is** the implementation and the repo's own
file is a thin host shim supplying only its document registry — the general
engine/shim rule is practice 50; this renderer is its strongest case, since
a spec-only export of "multi-sort with pinning and filters" reimplemented
from prose differs in a hundred details.

One renderer module (markdown → styled HTML, tables enhanced by
a small dependency-free script), one registry entry per document, renders
committed next to their sources, a line in each source pointing readers at
the render. Numeric sort keys must survive the units and approximations your
documents actually use (currency suffixes, ≈/≤/≥, thousands separators) —
extend the key parser when a new format appears, in the shared module, once.

**Related.** Practice 33 (documents track their models; transformations live
in code) supplies the live tables this renders; practice 12 (conventions
harden into audits) suggests the natural follow-on check — a registered
document whose render is stale fails the gate.
