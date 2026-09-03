<!-- Last updated: 2026-08-31 (Buenos Aires) by the phase-4 routing pass -->

# Pre-registered prediction for the next routing-eval run

**Written before the globs were applied, before any prompt was regenerated,
and before any cell was run.** It is committed in the same state it was
written; the result is reported against it whatever it says.

The reason for writing it down: this is the third change to the loader's
inputs in one phase, and re-running a measurement until it moves is how a
number stops meaning anything. The plan already forbids tuning the occasion
index to chase the recall figure. A glob pass is a different thing — the plan
names "a narrower glob" as the right response to a repeatedly-unrouted
practice — but it is close enough to the forbidden thing that the honest
protection is to say in advance what is expected and then not revise it.

## What changed

A pass over all 46 on-demand practices, recorded in
[tools/routing_scope.json](../../tools/routing_scope.json) with a reason for
every one. Ten gained a narrower `applies_to`; 24 stay at `**` with the reason
stated; 12 keep the glob phase 1 gave them.

**Three of the ten were in the v4 miss table** (`engine-plus-host-shims` ×3,
`session-bootstrap` ×1, `scripts-assert-properties` ×1). **Seven were not**,
and were given a glob on the merits alone. That ratio is deliberate: a pass
that only touched the practices which happened to miss would be fitting the
catalogue to twenty commits.

The standing instruction in the generated loader block also gains one line
naming the gate channel, so the treatment prompt changes for that reason too.
The run cannot separate the two.

## The prediction

1. **The specific practices should become surfaced.**
   `engine-plus-host-shims` should be surfaced by the path channel on the
   three cases it was missed on, and `session-bootstrap` and
   `scripts-assert-properties` on their one each. Whether the session then
   *names* them is the open question; surfacing is deterministic and
   surfacing is what changed.

2. **The aggregate will move less than it looks like it should, and may not
   move at all.** v4 already showed that surfacing a practice does not make a
   session name it: after the `practice-export-loop` glob fix, all four of its
   remaining misses were cases where the path channel had surfaced it and the
   session declined anyway. The same is likely here. **Expected: treatment
   recall up 0–8 points, which this eval cannot resolve and which will not be
   claimed as an effect.**

3. **Precision will fall and cost will rise**, because ten more practices now
   fire on files where they may not apply. This is the price of the pass and
   is the number to watch: if precision falls a long way, the globs are too
   wide and should be narrowed, regardless of what recall does.

4. **The 8 in-context misses will not move**, because nothing in this pass
   touches them. `verify-postcondition` (0 of 3) and `environment-gotchas` are
   resident and were already in front of the session.

5. **The gate channel is invisible to this eval.** It routes at moments the
   harness does not simulate. No part of any recall change can be attributed
   to it, and none will be.

## What would count as this pass having failed

- Precision falling below roughly 70% — the globs would be surfacing noise.
- Any of the three named practices still not surfaced by the path channel,
  which would mean a glob is wrong rather than merely unpersuasive.
- Cost per case rising by more than roughly a quarter, which would mean the
  saving the loader exists for is being spent on reach.

---

## Addendum, written before the run and after the globs were applied

The text above is left exactly as pre-registered. Two things changed between
writing it and running, and both are recorded here rather than edited into it.

**Two of the ten globs were withdrawn before the run, on the merits.** The
first draft surfaced 13.2 practices per case against a baseline of 8.6 — past
the "cost rising by more than roughly a quarter" line above. That figure is
what prompted a re-read; the re-read is what withdrew them, and the arguments
come from the practice text, not the cost:

- `scripts-assert-properties` → back to `**`. Its own Rule carries a scope
  gate: *"Scripts that own their own numbers end to end need nothing. Keep the
  instrumented list explicit."* A glob over `tools/**` surfaces the Rule on
  every script, which is precisely the over-instrumentation that gate forbids.
  The explicit list is the routing mechanism, and it already exists.
- `engine-plus-host-shims` → narrowed to the vendored tree and the host shims.
  Its occasion is *exporting* a tool across a boundary, which happens where
  the tool crosses, not in `tools/` where it is authored.

A third and fourth were narrowed for the same reason a round later
(`volatile-rules-carry-dates` back to `**`, `github-setup-disclosed` down to
the workflow files), which is where the rule this pass settled on came from:
**a glob is justified only where the path identifies the practice's
distinguishing condition, not merely a necessary one.** So **eight** practices
gained a glob, not ten, and the note in
[tools/routing_scope.json](../../tools/routing_scope.json) carries the rule.

**This is the honest risk in the pass, stated plainly:** narrowing a glob
after seeing a cost number is one step away from fitting the catalogue to the
measurement. The protection is that the rule was applied uniformly to all 34
candidates afterwards rather than to the expensive ones only, and that every
decision — including all 24 that stay at `**` — is written down with its
reason in a file the harness checks against the practice files.

**The prediction itself is unrevised.** The four failure criteria stand as
written, and the cost criterion is the one now in the most doubt.
