---
slug:        gate-ledger
title:       A gate that re-runs work to prove nothing changed keeps a ledger of verified facts
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus. A gate that re-runs work to prove nothing changed can live anywhere; the practice is a property of the gate tool, not of a path. Decided: 2026-09-28, with the practice."
occasion:    "writing, running or reviewing a gate, audit, cache or heavy solve"
gates:       []
index_clause: "re-runs: record code, reads and result per unit; skip a unit whose fact holds"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "Alex, 2026-09-28 -- asked for in session (\"Should we break them into smaller pieces and maintain a table that connect them to the cache of values they use?\"), then \"Let's do the fixes\""
strength:    decided
source_practice_number: null
---
## Rule
A gate that checks generated output (a document block, an audit's
verdict) by **re-running the script and comparing** spends nearly all of
its time proving that nothing changed. So it keeps a **ledger of verified
facts**, one per unit of work, and **skips a unit whose fact still holds**.
A fact records everything the result can depend on:

- the **fingerprint of the code the unit can reach** — the same engine that
  keys memos (practice
  [slow-steps-report-and-cache](slow-steps-report-and-cache.md)), taken from
  the unit's own entry point, not the whole script;
- the **files the run actually read, and the repository modules it loaded
  outside the fingerprint's static import closure**, each with a content
  hash — **recorded by an audit hook in the process that did the work**,
  never declared by hand;
- the **hash of the result**.

A unit whose fact holds on all three is not run. **Content hashes, never
timestamps**: a checkout or a merge rewrites every file's time.

## Detail
**Facts verify themselves, so the ledger merges by union.** Every line
says what it depends on and the gate re-hashes it; a stale or foreign
line costs one re-run, never a skipped unit. Mark the file `merge=union`
and commit it with the change that wrote it, so a fresh checkout starts
warm.

**No reads, no fact.** A run whose hook did not load, or whose process
died before it could list what it loaded, gets no fact and runs every
time. A failing unit is never recorded. An empty read list is a claim;
a missing one is not.

**The hook records reads, not the import system.** The import machinery
lists every directory it searches; those listings are where code is
found, which the fingerprint covers. Recording them made every new file
in a model directory re-run every model beside it.

**Count the whole static import closure as covered.** A module the unit
imports but never reaches cannot change its result, so its edits must
not re-run the unit; a module loaded **by file path** is outside the
fingerprint's sight and is hashed whole. Modules whose only effect is to
fetch or store a result — a memo loader, a shared-cache client — are
listed by the host as not counting.

**Cache the cheap-looking side work too.** A declaration step that looks
free (a script's list of the figures it owns, read by importing it) can
run the script's whole solve on import; it gets a fact of its own.

**A unit whose dependencies cannot be recorded gets no fact.** The hook
records what the work opened, listed, tested for existence and read from
the environment, each hashed at the moment it was read; a child that is
not Python, a process that did not load the hook, or a file that changed
while the run was reading it leaves the unit without a fact. A fact also
records the hook that saw its reads, so a change to what the hook watches
invalidates every fact taken under the old one.

**Some gates cannot be ledgered.** A test harness whose checks test the
environment itself (a file's existence in the harness's own process, git
and network calls made by tool children, state one check leaves for the
next) cannot be observed well enough: a sound ledger leaves nearly every
slow check without a fact, and an unsound one replays a PASS over a real
failure. Measure the sound version's saving before shipping one, and
do not ship it when the saving is small.

**The ledger is not a licence to skip the gate.** It makes the bare
gate cheap enough to run every time; a `--full` switch ignores it for
the rare case of distrust.

This practice has no repository-level check (`checked_by: null`), and on
purpose: it is a property of the gate tools, not of a repository's files,
and the harness tests the tools themselves — a held unit is skipped, and a
changed reached function, a changed read file, or a hand edit inside a
generated block each re-runs it.

**Test the skip against a full run on trees broken on purpose.** A
ledger's own tests are written by the person who believes it works, and
they pass. The test that finds the holes breaks one dependency per case,
runs the skipping gate beside a `--full` run, and requires the two
verdicts to agree. Give it one case for each kind of dependency the work
can have: a file's content, a file that goes missing, an existence test,
an environment variable, a child process, the network, state one unit
leaves for the next, and the clock. **Anything the hook cannot see means
no skip** — a kind of dependency the ledger does not record is a case
where it must refuse to hold a fact, and the test proves it refuses.

**The hashing is one shared engine.** What a read's signature is, and
whether a recorded set of reads still holds, is
[tools/content_record.py](https://github.com/alex137/BestPractice/blob/staging/tools/content_record.py);
the ledger keeps what is particular to facts (the reads hook, the code
fingerprint, the hook version). A gate that checks a fact inline instead
of asking the ledger drifts from it: one did, and it skipped the
hook-version comparison every other fact made.

## Why
The expensive part of a drift gate is almost never the comparison; it is
re-deriving what every unit prints. When nothing changed, all of that is
waste, and a gate that takes twenty minutes gets skipped, run on a subset
by hand (missing the unit that did drift), or trusted from memory.

## Story
In the originating repository a single pricing edit cost two hours and a
quarter, most of it re-running generated blocks that could not have
changed and waiting on gates that re-derived every model. Asked where the
time went, the owner proposed exactly this: *"maintain a table that
connect them to the cache of values they use, and then we can simply
look up if they are older than the values in the cache on which they
depend."* Two refinements came from building it: content hashes rather
than "older than" (checkouts reset every file's time), and recorded reads
rather than declared ones. The first version then re-ran eighty-two
blocks whenever a file was added beside a model, because the hook was
counting the import system's directory listings; the fix was to ignore
listings made by the import machinery. Measured afterwards: three
hundred and fifty-one blocks checked in twenty-two seconds on an
unchanged tree, and every block re-emitted identically on a cold run.

A review the next day found the first version unsound in ways its own
tests could not show: file hashes taken at recording time instead of at
reading time, environment variables and existence tests unrecorded, a
change to the hook not invalidating old facts, and the script itself
counted as data, which hid a real gap in the per-block narrowing. Each
was reproduced on a toy repository and fixed. The same review ran the
harness ledger against checks that truly failed and saw it replay eight
of nine as PASS. It was switched off, then removed: a sound version
would have skipped almost nothing.

## Install
Give each gate that re-runs work to compare its output a ledger file
(merged by union when committed, or local and ignored when the gate's
authority lives in CI), a fact per unit recorded only on a clean pass,
and a `--full` switch. Record reads with an audit hook in the process
that did the work, never by declaration. The shared engine is
`tools/fact_ledger.py`, over `tools/content_record.py`; the document gate and the model audit in this
repository use it. The harness has none, for the reason above.
