---
title:         "Open Items and Gotchas: The New Format and Migration Plan"
kind:          proposal
status:        drafted
opened:        2026-09-14
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "TODO.md and the gotchas index both capture mechanically and drain by hand, so both only grow. This is the specification for the replacement: one item is one permanently-named file, typed by kind, dated in its name, with every list generated rather than hand-kept — plus the ordered migration plan for this repo and for every repo that vendors this format."
---
# Open Items and Gotchas: The New Format and Migration Plan

**Nothing here is implemented.** This is a specification to review, not a
report of work done. It replaces an earlier draft that argued its way to
these decisions; that argument is not repeated here — only the result.

## The Problem, in One Paragraph

[TODO.md](../TODO.md) and the gotchas index both fill up by a mechanical
trigger — a merge, a mistake — and empty out only when a person happens to
prune them. Nothing expires on its own. [TODO.md](../TODO.md) is 114 items,
77 still open, and over half the file by volume is items already done that
nobody removed. The gotchas index went from 5 entries to 42 in two weeks. Both
problems have the same shape, so both get the same fix.

## The Fix, in One Paragraph

**One item is one file. The file is created once, is named for what it is and
when it was first noted, and never moves or gets renamed again.** Everything that
changes about the item — whether it's done, who it's waiting on, how strongly
it was decided — is a field inside the file, not a change to its name or
location. Every list a person reads (open items by kind, all open decisions,
gotchas due for a look) is generated from those fields on demand, the same way
[MAP.md](../MAP.md) is generated from `practices/*.md` today. Nothing is ever
hand-sorted into a list that can drift from the truth.

---

## Part 1 — The Open-Item Format

### Directory and Naming

```
todo/todo-2026-09-14-source-set-push-triggers.md
```

- **Directory:** `todo/`, replacing [TODO.md](../TODO.md).
- **Filename:** `todo-<YYYY-MM-DD>-<slug>.md`. The date is the day the item was
  first noted, at the front, so the directory sorts oldest-first with no tool
  involved (`ls todo/` alone shows age).
- **The `todo-` prefix is mandatory and marks the file as non-binding.**
  A practice file ([practices/verify-postcondition.md](../practices/verify-postcondition.md)) has no prefix,
  because a bare slug in this repository means a rule in force. `todo-` and
  `gotcha-` (below) exist so a slug like `cleanup-old-list-items` can never be
  misread as a practice: the unmarked namespace is the one that binds, and
  everything else says so in its own name.
- **The filename never changes after creation.** Closing an item, reassigning
  it, or changing how strongly a decision was made — none of these rename or
  move the file. Every link to it stays valid forever.

### Frontmatter

```yaml
---
slug:              todo-2026-09-14-source-set-push-triggers
kind:              analysis
domain:            mechanism
severity:          notable
status:            open
noted:             2026-09-14
closed:            null
blocked_on:        "a session rooted in each practice set"
waiting_on:        null
project:           source-sets
disposition:       wait
decision:          null
decision_strength: null
---
## What
## How It Closes
## Notes
```

| Field | Values | Meaning |
|---|---|---|
| `slug` | matches the filename, no `.md` | the item's permanent identity |
| `kind` | `analysis` \| `verify` \| `manual` \| `decision` | what KIND of work closes it — see **The Four Kinds** below |
| `domain` | `content` \| `mechanism` \| `null` | is this about the actual deliverable (a practice, a document) or about the machinery that manages it (a check, a hook, a workflow) — see **Domain** below |
| `severity` | `blocking` \| `notable` \| `minor` \| `null` | optional; how much this matters, for sorting the unblocked-work view — the first field to drop if the frontmatter gets too heavy |
| `status` | `open` \| `done` \| `dropped` | is it finished |
| `noted` | `YYYY-MM-DD` | the day this was first written down; must match the date in the filename, checked mechanically — **not** the day anyone reads or reopens the file. Where the true date is unknown, this is a floor (earliest known), and the file's own `## Notes` says so — see **Every Item Has a Date** below |
| `closed` | `YYYY-MM-DD` or `null` | when `status` became `done` or `dropped` |
| `blocked_on` | free text or `null` | the stated reason it isn't done now — required unless `status: open` and `kind: analysis` with no blocker, which is itself a finding (see Part 3) |
| `waiting_on` | a person's name, or `null` | who has to act next — a **label**, not a filing location, and not necessarily the person who will eventually do the work (see **Why Kind, Not Waiting-On** below) |
| `project` | free text, or `null` | groups items that are really one job, so they can be swept together |
| `disposition` | `wait` \| `ask` \| `parked` | unchanged from [open-item-disposition](../practices/open-item-disposition.md) — whether a session may raise it unprompted |
| `decision` | free text, or `null` | for `kind: decision` items only — what was decided, in prose, written when `status` becomes `done` (see **When an Item Closes** below) |
| `decision_strength` | `decided-strong` \| `decided-weak` \| `assented` \| `null` | only set where the item records an approval — see **Decision Strength** below |

### The Body Sections

Three, always, in this order:

- **`## What`** — what the item is, written once, rarely touched again.
- **`## How It Closes`** — the static condition: what has to be true for
  `status` to become `done`. This is `blocked_on` elaborated in prose.
- **`## Notes`** — an append-only, dated log. **Any session whose work
  touches this item without closing it adds a line here** — what it found,
  what it did, what changed. This is
  [item-closes-on-its-condition](../practices/item-closes-on-its-condition.md)
  given an actual place to write: that practice says work bearing on an item
  gets recorded into it, and until now nothing in the old format said
  *where*. A line looks like:

  ```
  2026-09-16: confirmed the API still returns the old shape; blocked_on unchanged.
  ```

  Notes are never edited or removed, only appended — the log is the point.

### The Four Kinds

This is not a new taxonomy — it already exists, unused, in
[templates/TODO.md.template](../templates/TODO.md.template). This format is
the first thing to actually use it.

| `kind` | Meaning | Closes when |
|---|---|---|
| **`analysis`** | Work a session can do from its own desk — read code, write code, run a check, write a document. | A session does the work. |
| **`verify`** | A claim that needs checking against something outside this repository — a live API, another repo's real state, a platform's current behavior. | The check is run and the result is recorded. |
| **`manual`** | Needs a person to actually DO something this session cannot — hardware, a vendor, a real end-to-end rehearsal. | The person does the thing. |
| **`decision`** | Needs a person to CHOOSE between options this session has already laid out. | The person decides. |

`manual` and `decision` are easy to confuse and worth separating cleanly:
`decision` is closed by a choice; `manual` is closed by an action. "Which
naming convention should we use" is a decision. "Run this on real hardware
and report what happened" is manual, even though a person is doing both.

**Why kind, not waiting-on, is the filing axis:** an earlier draft of this
plan filed items by "who can clear it" and got it wrong in the same breath —
four of five groups named a kind of work, not a person, and the one group
that did name a person ("Alex needs to decide this") was sometimes wrong
about which person. `waiting_on` is kept as a field precisely because it
needs correcting without anyone renaming a file. `kind` doesn't have that
problem: whether a task is analysis, verification, a manual action, or a
decision is a fact about the task, and it doesn't change hands.

### Domain

A second, independent axis: is this item about the actual deliverable, or
about the machinery that manages the deliverable?

| `domain` | Meaning |
|---|---|
| **`content`** | The item is about the thing itself — a practice's wording, a document's accuracy, a missing piece of the catalogue. |
| **`mechanism`** | The item is about the tooling, checks, hooks, or workflow that build, enforce, or ship the content. |
| **`null`** | Genuinely both, or neither — not every item needs a domain. |

**Why this isn't folded into `kind`:** `kind` says what closes an item;
`domain` says what it's about. A `content` item and a `mechanism` item can
both be `kind: analysis` — "fix this practice's wording" and "fix this
check's bug" are both a session doing the work from its desk, and knowing
that is useful independently of knowing which one it is. Cramming both facts
into one field would mean either doubling `kind`'s values (eight instead of
four) or losing one axis. Keeping them separate keeps `kind`'s meaning exact.

### Severity

Optional, and the field most likely to be cut if the frontmatter proves too
heavy in practice:

| `severity` | Meaning |
|---|---|
| **`blocking`** | Something else can't proceed until this closes. |
| **`notable`** | Worth attention, not urgent. |
| **`minor`** | Low cost either way. |
| **`null`** | Not assessed. |

Severity decays faster than `kind` or `domain` — what's blocking today may
not be next week — so it's the one field a session should feel free to leave
`null` rather than force a guess on. It exists for one purpose: letting the
unblocked-work view (Part 1, **Generated Views**) sort by something other
than age.

### Every Item Has a Date

**No item is ever dateless.** Every `todo/*.md` and `gotchas/*.md` file
carries a real date in its name, always — this is a hard rule, not a
default that some items opt out of.

**No dedicated field for precision.** An earlier draft carried
`noted_precision: exact | at-or-before` for this, and on review it isn't
worth a permanent field: the distinction matters for exactly one thing — the
batch of items migrated in with no true creation date — and every item
created from this point on has an exact date by construction (a session
creates the file today, dates it today). A field that is `exact` on every
future file forever, to serve a fixed, shrinking batch of legacy ones, is
the wrong trade.

**Instead: the file's own `## Notes` carries the caveat, once, at
migration.** For the items being migrated in whose anchor is already present
at the earliest commit this repository's history reaches — so the honest
statement is *at or before that date*, not a specific day — the filename
still uses that floor date (a name must be assigned; it's a lower bound, not
a guess), and the migration writes one line into `## Notes`:

```
2026-09-16: noted date is a floor, not exact — this item predates anchor
tracking and its true creation date is unknown. Migrated from TODO.md.
```

The generated index shows age the same way for every item, computed
straight from `noted`. For the legacy batch this slightly overstates
precision in the index; anyone who needs the caveat finds it in the one
place that actually states it, rather than the whole schema carrying a
field that means something for a few dozen files and nothing for the rest.

### When an Item Closes

**The file never moves.** Nothing in this format ever moves once created —
closing an item is a change to its fields, not to its name or location.

Setting `status: done` (or `dropped`) also sets `closed` to that day. For a
`kind: decision` item, it also sets `decision` — one or two sentences of
prose recording what was actually decided, written into the file, not left
implicit in the fact that `status` flipped.

**This repository also keeps [decisions/](../decisions/)** — a
longer-standing, higher-ceremony ledger for decisions with lasting,
citable weight, unrelated to this format and not being changed by it. The
two aren't duplicates: a `kind: decision` todo item answers "was this
settled," and a `decisions/` entry is "here is the record other documents
point back to." Most closed decisions need only their own `decision` field.
A decision significant enough to warrant the second treatment gets both —
same as today, where a session writing a `decisions/` entry is already a
separate, deliberate act.

### Decision Strength

**Extending this to the universal [decision-strength](../practices/decision-strength.md)
practice itself was raised in review, and it reopens a question that
practice's own Story records as already settled — against it:**

> A scale of three or five levels was considered and rejected in the same
> conversation: more resolution than the evidence supports, and an
> invitation for a session to split hairs about someone's state of mind —
> which is the invention this rule exists to stop.

`decided-strong` / `decided-weak` / `assented` is a three-level scale in
exactly the shape that passage describes. This isn't a reason not to do it —
the person who rejected it once is free to want it now, for a stated reason
— but it's the kind of thing that has to be seen before it's decided, not
discovered afterward. **So this is written up as the fourth Open Decision
below, not as settled**, with the plan ready to run the moment it's
confirmed.

**Sized, so the decision is made with real numbers:** `strength:` appears in
the frontmatter of **23 practice files**, and as an inline citation in
**49 files repo-wide** — `TODO.md` alone carries roughly two dozen. It is
also a *universal* practice, vendored into every dependent repository and
all four attached practice sets, so a change here propagates the way the
`todo`/`gotchas` format itself does (Part 4.2).

**If confirmed, the safe migration is a rename, not a re-judgment — and
that distinction is what keeps it from violating the practice's own
anti-backfill rule.** [decision-strength](../practices/decision-strength.md)
already refuses to backfill strength onto old *unmarked* approvals, because
guessing a past state of mind is exactly what
[no-invented-specifics](../practices/no-invented-specifics.md) forbids. That
rule is not violated by this migration, because nothing here requires a new
judgment about the past:

- **Every existing `decided` becomes `decided-strong`.** The universal
  practice's own definition of `decided` — *"they asked for it, chose it
  from options you laid out, or pushed back and the thing landed where it
  landed"* — already describes conviction, not ambivalence. Relabeling it is
  a mechanical rename, not a new read of anyone's state of mind.
- **Every existing `assented` is untouched.**
- **`decided-weak` is forward-only.** Nothing in the historical record was
  ever assessed against a category that didn't exist yet, so nothing is
  reclassified into it. It starts being used the day this lands, for a "sure,
  I guess" that today gets written down as a plain `decided` it wasn't.
- **The field key stays `strength:`.** Only the legal values widen. Renaming
  the key too would double the migration surface (23 frontmatter blocks, 49
  files of prose) for no benefit this format's own `decision_strength` key
  doesn't already get from being new.

**In this format**, `decision_strength` uses the same four-value vocabulary
(a distinct key, per the naming-collision reasoning above). It is set only
on items that actually record an approval; most items are findings nobody
approved, and writing a decision strength on those would be recording an
approval that never happened. It is set going forward, when an item is
touched, never backfilled in bulk against old items — the same rule as the
universal practice, unchanged either way this is decided.

### Generated Views

**`todo/TODO.md`** — same familiar name as today's root-level file, now
inside the directory it indexes, generated the way [MAP.md](../MAP.md) is
from `practices/*.md`. Its own first line says so, so nobody mistakes it for
something to hand-edit:

```
<!-- GENERATED by tools/build_todo_index.py — do not edit. Edit the item
     files in todo/ instead; this file is rebuilt from their fields. -->
```

It carries at minimum:

- **One table per `kind`**, with `domain` and `severity` as columns.
- **Age**, computed from `noted`, sorted oldest first.
- **Unblocked work** — every `open`, `kind: analysis` item with no
  `blocked_on`. This is the list that should be closest to empty.
- **Open decisions** — every `open`, `kind: decision` item, the one list a
  person is actually asked to read regularly.
- **Done items**, last, one line each.

A hand-kept file drifts the moment a `blocked_on` clears and nobody moves the
item. A generated view can't drift, because it's rebuilt from the fields
every time — this is the whole reason the format is a directory of small
files with fields, rather than a bigger hand-edited document.

---

## Part 2 — The Gotcha Format

Same shape, adapted to what a gotcha is: a trap recorded so the next session
doesn't rediscover it, not a piece of unfinished work.

### Directory and Naming

```
gotchas/gotcha-2026-09-13-shallow-clone-reads-as-diverged.md
```

Same rule as `todo-`: dated, prefixed, permanent once created.

### Frontmatter

```yaml
---
slug:            gotcha-2026-09-13-shallow-clone-reads-as-diverged
status:          live
noted:           2026-09-13
severity:        notable
retired:         null
retires_when:    null
---
## Symptom
## Story
## Fix
```

| Field | Values | Meaning |
|---|---|---|
| `status` | `live` \| `retired` | replaces the separate [record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md) file — a retired entry is the same file, `status` flipped, never moved |
| `severity` | `blocking` \| `notable` \| `minor` \| `null` | optional, same three values as the open-item format — here it means how costly the trap is when hit, not how urgent it is to fix |
| `retires_when` | free text, or `null` | the condition under which this entry stops being worth a session's attention — declared in the schema now, **populated later**; see below |

### `retires_when` Is Declared Now, Built Later

Today nothing states what would retire a gotcha; an entry is archived only
when a person happens to re-read it and judge it dead. The field is part of
the schema from the start — so no gotcha file needs a second migration later
— but it is **not populated as part of this migration**. Writing it on the
42 live entries, and wiring the sweep in Part 3 to read it, becomes the
first real `kind: analysis` item filed in the new `todo/` system once it
exists — a fitting first use, and a small, well-scoped task rather than
something this migration has to carry.

When it is built, three shapes should cover nearly every case:

```
retires_when: "a mechanical check refuses this — <name the check>"
retires_when: "the harness fixes <specific behavior>; re-test whenever
               the harness changes that behavior"
retires_when: "nothing has hit this since <date> and the mechanism
               that caused it no longer exists"
```

### Generated View

The gotcha index inside [AGENTS.md](../AGENTS.md) stays exactly as it is
today — one line per live entry, symptom plus link, loaded every session. It
is generated from `gotchas/*.md` where `status: live`, instead of hand-kept.
`retires_when` is deliberately **not** shown there even once it's built:
it's read by whoever is auditing the catalogue, not by every session that
pays for the index.

---

## Part 3 — The Two Sweeps

Both are additions to `python3 tools/very_deep_check.py`, run on request, not
on a schedule — this repository has no mechanism for "review this
periodically," and adding one is out of scope here.

**Open-item sweep.** Reads every `todo/*.md` and reports, without closing
anything:
- Every `open`, `kind: analysis` item with no `blocked_on` — these should
  either be done now or have a real reason written down.
- Every item whose `blocked_on` names something that no longer exists.
- The oldest few items by age.

**Gotcha sweep.** [tools/very_deep_check.py](../tools/very_deep_check.py)
already has a gotcha-currency pass that follows the index into the record and
reads the bodies (120-day staleness threshold, measured, not assumed). It's
extended to read `retires_when` and report entries whose condition looks met.

Neither sweep closes or retires anything on its own —
[item-closes-on-its-condition](../practices/item-closes-on-its-condition.md)
already puts that judgment on a person or the session doing the work, and a
heuristic auto-closer would undo it.

---

## Part 4 — Migration Plan

### 4.1 — This Repository

Ordered; each step is independently useful, so nothing is wasted if a later
step is deferred.

1. **Fix the already-broken references first.** `TODO.md` is cited by number
   in prose in five tool files ([tools/precedent_check.py](../tools/precedent_check.py),
   [tools/verify_harness.py](../tools/verify_harness.py), and others) — these numbers shift on every
   insert and are wrong today, independent of anything else in this plan.
   Repoint them to anchors.
2. **Prune done items out of `TODO.md`.** Under the new format these become
   `status: done` files; under the old format, moving them out is the same
   work either way, so do it now rather than migrating dead weight.
3. **Delete the visible numbers from `TODO.md`.** Nothing can then be cited
   by a number that's about to stop meaning anything.
4. **Write the frontmatter schema and the generator as real code** —
   `tools/todo_migrate.py` (one-time, item-by-item conversion) and
   `tools/build_todo_index.py` (ongoing, run the way [tools/build_views.py](../tools/build_views.py) is).
5. **Run the migration.** Every live item in `TODO.md` becomes a
   `todo/todo-<date>-<slug>.md` file. Every entry in
   [record/GOTCHAS.md](../record/GOTCHAS.md) and
   [record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md) becomes a
   `gotchas/gotcha-<date>-<slug>.md` file, `status: retired` for the archived
   ones. Every item with no true creation date gets its floor date and the
   one-line `## Notes` caveat (**Every Item Has a Date**). The migration
   commit includes a full old-slug → new-filename mapping table.
6. **Repoint every existing reference** using that mapping table
   ([rename-updates-links](../practices/rename-updates-links.md)) — the
   `TODO.md#slug` links, the `#gN` gotcha anchors, everywhere they appear in
   `spec/`, [AGENTS.md](../AGENTS.md), and practice files.
7. **Add a check that fails on a stale reference** — a link to `TODO.md#x`,
   a bare `#gN` anchor, or an `item N` phrase, anywhere in the tracked tree,
   from this point on. Without this the migration decays within a week.
8. **Wire the two sweeps into `very_deep_check.py`** (Part 3), last, because
   they read fields the migration creates.
9. **File `retires_when` on the 42 live gotchas as the new system's own first
   `todo/` item.** Not part of this migration (Part 2, **`retires_when` Is
   Declared Now, Built Later**) — its natural home is the system it will run
   in.

**`domain` and `severity` are not required at migration time.** The migration
script sets `kind`, `status`, `noted`, `blocked_on`, `waiting_on`, and
`disposition` from what the old item already states — those are read off the
existing text. `domain` and `severity` are left `null` on every migrated item
rather than guessed at for 114 items in bulk; a session sets them when it
next touches an item, the same rule as `decision_strength`.

### 4.2 — Dependent Repositories

This format lives in [templates/TODO.md.template](../templates/TODO.md.template)
today, which every adopting repository instantiates — so this plan is not
this repository's alone. **There is no single old format to convert from**:
measured across the four attached practice sets, one has a `TODO.md` with
4,344 words and zero anchors, one has three numbered items, and two have no
`TODO.md` at all.

The sequence for a dependent repository:

1. **This repository ships the finished template and tooling first** — the
   frontmatter schema, `tools/todo_migrate.py`, `tools/build_todo_index.py`,
   and the stale-reference check, all vendored the way the rest of the engine
   is.
2. **Each dependent repository migrates from a session rooted in it**, running
   `tools/todo_migrate.py` against its own `TODO.md` (or starting a fresh
   `todo/` if it has none) — never migrated from this repository on the
   dependent's behalf, since only a session rooted there can see what that
   repository's items actually mean.
3. **A repository with no `TODO.md` today just starts using `todo/`** — there
   is nothing to migrate, only the template to adopt.

### 4.3 — What Does Not Migrate Automatically

**Gotchas are this repository's own environment lore and do not travel to
dependent repositories the same way.** [record/GOTCHAS.md](../record/GOTCHAS.md)
describes traps in *this* codebase's tooling; a dependent repository's own
environment gotchas (if it keeps any) are a separate, repository-local
collection under the same format, not a copy of this one's.

---

## Part 5 — Cost, and What Was Deliberately Left Out

**Per-item overhead goes up, and this revision made it heavier.** A one-line
open item becomes a file with fourteen frontmatter fields. Four of them
(`domain`, `severity`, `decision`, `decision_strength`) are optional and can
sit `null`, so the mandatory core is closer to the original ten — but every
field in the schema is a field a reader scans past on every file, whether or
not it is set. The median live item today runs to a few hundred words, where
this costs nothing; the shortest is under thirty words, where the frontmatter
is most of the file. Taken anyway, because the alternative — one file no tool
can slice, that every session reads in full — is worse at the current and
growing size (114 items, 42 gotchas). `severity` (see Part 1) is named
explicitly as the field to cut first if this proves too heavy in practice.

**Left out of this plan on purpose:**

- **A scheduled review.** The sweeps in Part 3 run on request
  ([very-deep-check](../practices/very-deep-check.md)'s own standing rule),
  not on a timer. This repository has no periodic-schedule mechanism, and
  building one is a separate decision.
- **Four hand-kept files instead of a generated index.** A variant worth
  naming: keep `todo/decisions.md`, `todo/unblocked.md`, etc. as real,
  hand-visible files rather than one generated `todo/TODO.md`. Not taken
  here, because a hand-kept file whose `blocked_on` has cleared lies until
  someone moves the item — but it is a legitimate choice if the generator
  turns out to be more friction than it's worth in practice.
- **Auto-closing items or gotchas from a sweep.** Both sweeps report only;
  closing stays a human or an active-session judgment
  ([item-closes-on-its-condition](../practices/item-closes-on-its-condition.md)).
- **Populating `retires_when` on the existing 42 gotchas now.** Deferred to
  a follow-up item filed in the new system itself (Part 4.1, step 9).

---

## Open Decisions

Four things this plan does not settle, each independent:

1. **The rule for items with `kind: analysis`, `status: open`, and no
   `blocked_on`.** Today these exist and nothing says what should happen to
   them. Two live options: **(a)** fix-on-sight — a session that finds one it
   can fix, fixes it, and the sweep in Part 3 closes anything left with no
   stated blocker; **(b)** leave them queued, accepting that some real work
   sits unfinished with no mechanical pressure on it. (a) is the only option
   that keeps the unblocked-work list meaningfully close to empty; the cost is
   that it turns every audit finding into an unplanned detour, and some of
   these are real multi-hour jobs, not quick fixes.
2. **Whether `todo/TODO.md` is one generated file or several hand-kept
   ones** (Part 5, second bullet).
3. **Whether the full migration (Part 4) is worth doing now**, versus doing
   only steps 1–3 of §4.1 (fixing broken references, pruning done items,
   removing visible numbers) and deferring the file-per-item split. Steps 1–3
   are reversible and useful regardless of the rest of this plan; steps 4
   onward are the commitment.
4. **Whether to extend the universal [decision-strength](../practices/decision-strength.md)
   practice to `decided-strong` / `decided-weak` / `assented`, and migrate
   all 49 files that currently use it** (Part 1, **Decision Strength**).
   Raised in this review; sized and a safe migration mechanism proposed
   (relabel `decided` → `decided-strong`, leave `assented` alone,
   `decided-weak` forward-only — no historical case is re-judged). **The one
   thing that has to be weighed knowingly:** the practice's own Story records
   a three-to-five-level scale being considered and rejected in the
   2026-09-09 conversation that created it, for a stated reason — more
   resolution than the evidence supports, inviting a session to split hairs
   about someone's state of mind. This proposal is exactly that shape. Worth
   doing for a reason that holds up against that history, not by default.

---

## Appendix — Item Classification, Measured 2026-09-14

The table below classifies the 57 items that were open on 2026-09-14, by the
five kinds of work found in the file at that time — evidence for why the
`kind` field above is the right axis, not a live count. **The repository has
moved since** (114 items as of this writing, up from 91); re-run this
classification against the current file before using it to plan actual
migration work.
### The 57, Classified

Each row links the item. `Since` is the first day its anchor appears in the
file's history; `Words` is how long the item has grown.


### A. Source-Set Work — 18 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`roll-out-four-pass-restructure`](../TODO.md#roll-out-four-pass-restructure) | ≤09-06 | 262 | wait | Roll the very deep check's four-pass restructure out to `precedent-team-repo-maintenance`' own `deep-check` |
| [`attach-private-sources`](../TODO.md#attach-private-sources) | ≤09-06 | 883 | wait | Run one session rooted at each private set — this unblocks four other items at once |
| [`source-repo-consumes-no-catalogue`](../TODO.md#source-repo-consumes-no-catalogue) | ≤09-06 | 120 | wait | A source repo consumes no catalogue, so it cannot check itself |
| [`decision-strength-private-sources`](../TODO.md#decision-strength-private-sources) | 09-09 | 167 | wait | Carry `decision-strength` into the two private practice sets |
| [`source-hook-drift`](../TODO.md#source-hook-drift) | 09-09 | 1480 | wait | Decide whether a drifted-but-present session hook in a practice-set source gets brought up to canonical automatically |
| [`stale-days-does-not-travel`](../TODO.md#stale-days-does-not-travel) | 09-10 | 325 | wait | Decide whether the four private practice sets should declare their own `branch_stale_days` |
| [`source-load-ceilings`](../TODO.md#source-load-ceilings) | 09-11 | 150 | wait | Declare session-load ceilings in the attached practice-set sources, and measure the real total a session pays |
| [`provenance-check-skips-in-a-source-set`](../TODO.md#provenance-check-skips-in-a-source-set) | 09-11 | 828 | wait | A universal practice's mechanical check could not bind a source set, so sets relied on checks that silently skipped there |
| [`source-sets-vendor-the-broken-clause-matcher`](../TODO.md#source-sets-vendor-the-broken-clause-matcher) | 09-11 | 227 | wait | All four practice-set sources vendor the pre-fix `Source:` clause matcher |
| [`source-name-check-cannot-run-in-a-hosted-session`](../TODO.md#source-name-check-cannot-run-in-a-hosted-session) | 09-11 | 299 | wait | The source-name check reports UNVERIFIED for every private source in a hosted session, which is where most vendor updates happen |
| [`source-sets-declare-adapters`](../TODO.md#source-sets-declare-adapters) | 09-12 | 183 | wait | Have the private source sets declare their harness adapters |
| [`views-drift-vs-suite-workflow`](../TODO.md#views-drift-vs-suite-workflow) | 09-13 | 335 | wait | Decide whether a source set that runs the whole check suite in continuous integration should still carry `views-drift.yml` |
| [`wire-individual-hook-in-existing-sets`](../TODO.md#wire-individual-hook-in-existing-sets) | 09-13 | 467 | wait | Wire `precedent-individual-bootstrap.sh` into the four practice sets that already exist |
| [`source-set-runs-no-universal-checks`](../TODO.md#source-set-runs-no-universal-checks) | 09-13 | 406 | ask | A practice set now READS the universal rules and still RUNS none of universal's mechanical checks |
| [`vendor-very-deep-check-into-sets`](../TODO.md#vendor-very-deep-check-into-sets) | 09-13 | 475 | ask | Vendor `very_deep_check.py` into the practice sets, so a set can audit its own always-loaded files instead of only gating new ones |
| [`source-set-push-triggers`](../TODO.md#source-set-push-triggers) | 09-14 | 397 | wait | The four practice sets still run their checks on `pull_request` only, so a direct push to one runs nothing |
| [`set-ci-skips-vendored-tests`](../TODO.md#set-ci-skips-vendored-tests) | 09-14 | 166 | wait | No practice set's CI runs the vendored checks' own test suite, so a red suite sits under a green pull request |
| [`set-cannot-show-a-universal-practice`](../TODO.md#set-cannot-show-a-universal-practice) | 09-14 | 317 | wait | In a practice SET, `precedent_show.py SLUG` cannot read any universal practice — and the generated file that delivers those practices tells its reader to run exactly that command |

### B. Engine Defects, Nothing Blocking — 16 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`unreachable-practices`](../TODO.md#unreachable-practices) | ≤09-06 | 757 | wait | Populate `not_binding` for the practices in force here that do not bind this repo |
| [`background-freshness-fetch`](../TODO.md#background-freshness-fetch) | ≤09-06 | 229 | wait | Consider making the freshness check's fetch asynchronous |
| [`upstream-notice-silent-when-rooted-above`](../TODO.md#upstream-notice-silent-when-rooted-above) | 09-08 | 218 | wait | The upstream-carry notice is silent in exactly the layout this project requires, and nothing reports its absence |
| [`small-calls-vs-brainstorm`](../TODO.md#small-calls-vs-brainstorm) | 09-08 | 253 | wait | `small-calls` tells a session to commit during a brainstorm, and nothing mechanical stops it |
| [`sync-refuses-a-rewind`](../TODO.md#sync-refuses-a-rewind) | 09-10 | 277 | wait | Make `precedent_sync_views.py` refuse a sync that would rewind a practice's content, not just one that would remove the practice outright |
| [`private-owner-allowlist-inert`](../TODO.md#private-owner-allowlist-inert) | 09-10 | 662 | wait | The repo-reference allowlist is inert here, and this public tree names the account that owns the private practice sets |
| [`session-practices-reports-unresolved-sources`](../TODO.md#session-practices-reports-unresolved-sources) | 09-11 | 233 | wait | `.precedent/SESSION_PRACTICES.md` can report a source as unresolved that resolved fine minutes later — and a session reading it believes those practices are absent |
| [`consumer-views-drift-uncheckable-in-ci`](../TODO.md#consumer-views-drift-uncheckable-in-ci) | 09-11 | 266 | wait | A consuming repo's generated loader block cannot be drift-checked in CI, and today nothing checks it anywhere |
| [`renamed-team-source-not-in-allowlist`](../TODO.md#renamed-team-source-not-in-allowlist) | 09-11 | 584 | wait | Nothing checks that a rename carried its allowlist entry |
| [`figures-reach-commit-messages-ungated`](../TODO.md#figures-reach-commit-messages-ungated) | 09-11 | 512 | wait | A figure can reach a commit message without anything checking it, and it did twice in two days |
| [`source-clause-check-reads-only-html-comments`](../TODO.md#source-clause-check-reads-only-html-comments) | 09-11 | 226 | wait | The `Source:` clause check reads only HTML comments, so a generated file whose header is a `#` comment is never asked for one |
| [`consuming-repo-clause-clears-on-vendor-update`](../TODO.md#consuming-repo-clause-clears-on-vendor-update) | 09-11 | 156 | wait | Confirm the consuming repo's `Source:` clause actually clears, rather than assuming it |
| [`reply-check-cannot-forbid`](../TODO.md#reply-check-cannot-forbid) | 09-14 | 281 | wait | The reply check can only REQUIRE text, never forbid it — so every practice about what a reply must NOT contain is unenforceable by it |
| [`consumer-cannot-resolve-upstream-commit`](../TODO.md#consumer-cannot-resolve-upstream-commit) | 09-14 | 1738 | ask | A consumer repo cannot read upstream's own text at `upstream.commit` — nothing local resolves it — so no check that runs there may assume it can |
| [`engine-root-in-a-vendored-tree`](../TODO.md#engine-root-in-a-vendored-tree) | 09-14 | 205 | wait | Five engine tools read the wrong repo when vendored, and five more have not been checked |
| [`sync-views-blames-a-dropped-source-for-a-retirement`](../TODO.md#sync-views-blames-a-dropped-source-for-a-retirement) | 09-14 | 167 | wait | A retired practice is reported as one whose SOURCE was dropped, and a renamed source would read identically |

### C. Decisions — 10 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`github-issues-for-open-items`](../TODO.md#github-issues-for-open-items) | ≤09-06 | 46 | wait | Evaluate GitHub Issues for open items |
| [`reduce-github-dependency`](../TODO.md#reduce-github-dependency) | ≤09-06 | 72 | wait | Reduce GitHub dependency when ready |
| [`individual-practice-scoping`](../TODO.md#individual-practice-scoping) | ≤09-06 | 68 | wait | `for_team:`/`in_repos:` individual-practice scoping |
| [`retire-merge-target-practice`](../TODO.md#retire-merge-target-practice) | ≤09-06 | 897 | wait | Retire local/practices/merge-target-is-beta-branch.md (and its check at local/tools/checks/check_merge_target_is_beta_branch.py, and the pointer in AGENTS.md's opening paragraph) the moment Alex reviews and merges `precedent-beta-v01` into `main` for real |
| [`relax-the-pinned-branch-hold`](../TODO.md#relax-the-pinned-branch-hold) | ≤09-06 | 418 | wait | Relax the pinned-branch hold once the fix has run through real sync cycles |
| [`review-skill-level-permissions`](../TODO.md#review-skill-level-permissions) | 09-10 | 629 | ask | Review the whole technical/non-technical permission split, now that the pieces are in three separate places |
| [`repo-name-regex-shape`](../TODO.md#repo-name-regex-shape) | 09-11 | 292 | wait | Think about the shape of the leak gate's repository-name rule: it refuses `owner/name` and ignores `name` |
| [`my-options-includes-doing-nothing`](../TODO.md#my-options-includes-doing-nothing) | 09-12 | 145 | wait | Decide whether "My options" must always list the do-nothing option |
| [`universal-adapters-undeclared`](../TODO.md#universal-adapters-undeclared) | 09-12 | 160 | wait | Decide whether THIS repository declares its own harness adapters |
| [`reply-check-rollout`](../TODO.md#reply-check-rollout) | 09-13 | 538 | ask | Roll the blocking reply check out to the sources that want one, and land the individual set's half |

### D. Waiting on the Outside World — 5 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`plain-chatgpt-write-support`](../TODO.md#plain-chatgpt-write-support) | ≤09-06 | 43 | wait | Re-verify plain-ChatGPT write support |
| [`grok-workflow`](../TODO.md#grok-workflow) | ≤09-06 | 28 | wait | Verify a Grok workflow |
| [`companion-mobile-app`](../TODO.md#companion-mobile-app) | ≤09-06 | 66 | wait | Companion mobile app, if the Shortcut proves insufficient |
| [`additionalcontext-reaches-the-model`](../TODO.md#additionalcontext-reaches-the-model) | ≤09-06 | 194 | wait | Confirm `additionalContext` actually reaches the model, not just the transcript |
| [`cross-owner-add-repo-push`](../TODO.md#cross-owner-add-repo-push) | 09-09 | 258 | wait | Measure whether `add_repo` refuses a cross-owner attachment in the REVERSE direction, with `access: "push"` |

### E. Waiting on a Project, Person or Phase That Does Not Exist Yet — 8 Items

| Item | Since | Words | Disp. | What it is |
|---|---|---|---|---|
| [`actions-as-enforcement-layer`](../TODO.md#actions-as-enforcement-layer) | ≤09-06 | 128 | wait | Lean further into GitHub Actions as the enforcement layer |
| [`out-of-chat-notifications`](../TODO.md#out-of-chat-notifications) | ≤09-06 | 58 | wait | Out-of-chat change notifications for members |
| [`contributor-access`](../TODO.md#contributor-access) | 09-11 | 175 | wait | Run the contributor-access plan for real |
| [`document-project-pilot`](../TODO.md#document-project-pilot) | ≤09-06 | 67 | wait | Run the document-project pilot once Morgan has a real first project |
| [`gates-absent-from-main`](../TODO.md#gates-absent-from-main) | 09-07 | 416 | wait | Put the leak gate on `main`; the deep check cannot go there until the merge-back |
| [`whatsapp-bridge-research`](../TODO.md#whatsapp-bridge-research) | 09-09 | 515 | wait | Verify the chat bridge's platform claims against the platforms, or drop it |
| [`audit-trail-item-placement`](../TODO.md#audit-trail-item-placement) | 09-09 | 165 | wait | Confirm where the audit-trail item belongs in philosophy/AI_GOVERNANCE_TO_COCREATE.md |
| [`retire-a-practice-source`](../TODO.md#retire-a-practice-source) | 09-10 | 276 | wait | Write the retirement sequence for a practice SOURCE, from the one real run |

