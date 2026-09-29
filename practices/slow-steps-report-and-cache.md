---
slug:        slow-steps-report-and-cache
title:       A step that runs longer than a minute reports progress, and a heavy pure solve is memoized to disk
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A property of how long something runs, not of where it lives -- a gate script, an audit and a heavy solve are all in scope and share no path. Reached through the occasion index. Decided: 2026-09-08, when the practice landed."
occasion:    "writing or running a gate, audit or solve over a minute"
gates:       []
index_clause: "print elapsed and remaining; cache a heavy solve to disk"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Alex, 2026-09-08 — merged on main as catalogue entry 55, a check-in from dependent repo #1"
source_practice_number: null
---
## Rule
Two mechanics, one motive — a long wait must never be blind, and it must
never be repeated for nothing:

- **Progress with an estimate.** Any step expected to run for more than about
  a minute prints, on its error stream, a periodic line with items done,
  elapsed time, and an estimated time remaining computed from the rate so far
  — every N items, or on a timer — and a chained gate script echoes each
  step's elapsed seconds into its log so the next person can quote expected
  durations instead of rediscovering them. Record those durations where the
  run instructions live, dated.
- **Memoize the expensive pure function to disk.** When several gates (a
  self-check, a drift gate that spawns one subprocess per generated block, an
  audit) each re-derive the same expensive table, cache the solved result
  under a gitignored directory, keyed by **a hash of the code the solve can
  reach** — the syntax trees of the functions and constants it can run,
  followed from its entry points across the repository's modules
  (`tools/reach_key.py`), widening to a whole module wherever the reach
  cannot be followed — never a timestamp, never the calling process's
  import set (a caller-dependent key produces one entry per caller and
  never hits). Load the cache lazily at **every** entry point, not
  only the first one written, and keep an environment switch that forces a
  fresh solve: the cache is an accelerator, never a dependency.

## Detail
**Profile before declaring the remainder "the next lever."** A two-minute
profile removed the whole remainder twice in the originating case.

**Lazily, at every entry point** is the half that gets missed. A cache loaded
only where it was first needed leaves every other caller paying full price,
and the run looks exactly as slow as it did before — which reads as the cache
not working rather than as the cache not being consulted.

**A memo is re-keyed only through a reproduction check.** When a source
edit moves the key, copying the stored results under the new key is allowed
only after re-evaluating every stored solution on the current code: a family
whose rows all reproduce is copied, a family with one row that does not is
re-solved. Any solve-side edit can change every stored answer, however
unrelated it looks, and a copied memo then publishes numbers the committed
code no longer produces. Two companions: a key that excludes a presentation
tail of the source must match its marker **at the start of a line** — the
marker's literal inside the key function itself is an earlier occurrence,
and matching the bare text truncates the hashed body there, so no edit below
that function ever moves the key; and a heavy search never runs from a
stdin or `-c` main under a process pool — a worker spawned from such a main
re-imports `<stdin>`, dies, and is respawned forever, which reads as "a task
that has been running for a long time".

**Follow a class a method at a time.** Reaching a class hashes its
shell (bases, decorators, fields); a method is hashed only when reached
code names an attribute of that name, and dunder methods always are.
Hashing the whole class ties a solve to every method of a shared record
type — in the originating repository, a change to one pricing method
re-keyed a geometry solve that never called it.

**Split a memo by what invalidates it.** When one solve produces an
expensive part (a geometry fit, a sizing search) and a cheap part computed
from it (a cost rollup, a ranking), memoize the expensive part's **state**
— enough to rebuild the solved object with one cheap evaluation — under a
key that stops at the cheap part, and recompute the cheap part every time
(or under a second memo keyed on everything). A memo that consumes another
memo's answer keys on **that answer**, not on the code that produced it
(early cutoff): an edit that re-solves the first without changing its
answer leaves the second warm. Verify the rebuild at solve time, against
the figure the solve itself computed, with a tolerance set by measuring
how much the solve's figure depends on what the process did before it; a
rebuild that is exact whatever came before is the better-defined figure.

**Count where a conservative fallback fires.** When a key cannot follow
something (a module loaded by a path it cannot name, a lookup it cannot
resolve), falling back to hashing more is sound. It is also silent: one
unresolved load can make a key cover the whole repository, and every
edit then re-solves. Ship the fallback with a census — scan every real
key and list where the fallback fired — and treat each firing as a gap
to close. The goal is zero firings in practice.

## Why
A gate that takes twenty minutes gets skipped, run concurrently with its
siblings (halving both), or trusted from memory. And a wait with nothing on
the screen is indistinguishable from a hang, so the operator either kills a
healthy run or waits on a dead one.

## Story
The originating case ran an eleven-fold re-solve per gate pass — one per
subprocess, nothing persisted between them. The first cache keyed on the
process's imports and never hit. The self-check then still ran nine minutes,
because a serial block executed *before* the cache load. And the owner's
question — *"do you have an estimate of how long we should expect to
wait?"* — had no answer, because nothing had ever measured it.

The re-key rule came a week later, from the same repository. A term added
for one operating mode changed the result of every published row in the
other mode; the memos were copied across the key change, and the numbers in
the study no longer reproduced from the committed code — found only when the
next question needed a stored solution re-run. The same day, three models
turned out to have keys that had never covered anything below their own key
function, because the marker that trims the presentation tail was matched
as bare text, so their memos had gone stale unnoticed.

The key and the split came three weeks later, from one pricing edit that
cost two hours. A rate constant moved; the fingerprint then covered the
whole record class, so it re-keyed a sizing sweep of five hundred variants
(six minutes) and an engine sweep (eight) that never used the rate. The
sweeps stored their prices beside their sizes, so even a method-level key
could not spare them. Split into a sizing memo and a pricing pass that
rebuilds each variant from its stored state in seventeen milliseconds
(against three and a half seconds to size it), a pricing edit re-prices
in seconds. The solve-time check first disagreed at the fifth figure; the
measurement showed the rebuild exact in any order and after any other
work, and the solve's own figure dependent on what its worker had sized
before — the old memo's last digits had depended on how the pool
scheduled the variants.

## Install
Memoize the solve under a source-content key with a bypass switch; add a
progress line with an estimate to anything over a minute; run heavy gates
sequentially; record measured durations, dated, in the run instructions;
export the pattern to any other heavy model the moment it appears.
A memo on a container's disk dies with the container: to share it across
sessions, see [shared-result-cache](shared-result-cache.md).
