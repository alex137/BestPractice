<!-- Written and committed before any prompt was answered. -->

# Pre-registered prediction — the synthetic occasion-routing stress test

Requested directly: confidence, before phase 5, that the current loader
reduces the missed-practice rate rather than just moving it around. The
existing six-round routing_eval.py program (v1-v5 + review/gloss/hop2 arms,
see spec/ATTENTION_CEILING.md) already answered the raw-recall version of
that question, unfavorably: control (all 53 practices, carry-everything)
misses 16%, treatment (the loader) misses 23%. Enforcement now covers 68%
of the treatment arm's remaining misses (15 of 22), which the existing
`routing_eval.py --enforcement` reports, but that is coverage, not a new
recall measurement.

Two attempts to source a genuinely fresh, non-cherry-picked case set failed:
this repo's own history is 100% self-referential (every commit is about the
practice engine itself, checked directly), and `main` vs `precedent-beta-v01`
turned out to be nearly synced after a proper unshallow fetch (only one real
commit of divergence, practice 53 -- a separate, already-actioned finding).
An external repo (WorkingWithAI) could not be attached in this session.

## What this run is, and is deliberately not

Eight synthetic tasks in a fictional small repo ("Lantern"), not real
commits (`evals/routing_synthetic/cases.json`). Each is **hand-written to
exercise one specific occasion-index entry** -- a practice reachable only
through the occasion index's prose, never a path glob -- because that is
where spec/ATTENTION_CEILING.md's own case-level diagnosis says the loader
actually loses ground (34 of 46 on-demand practices have no glob at all).

**This is a targeted stress test of one channel, not a representative
sample.** It answers a narrower question than the six-round program did:
*when the only signal is the occasion prose, and nothing else, does the
loader's two-hop read of that prose recognize the occasion at all* -- not
"what is the overall miss rate on real work." Read it as that, not as a
replacement figure for the 16%/23% headline.

**A stated bias, not discovered after the fact:** the person building the
case set (this session) also knows the practice catalogue, so cases were
picked to cleanly exercise a target occasion each -- this is closer to
"can the channel work when the signal is unambiguous" than "does it work on
messy real work where signals compete." A synthetic case's oracle answer is
also this session's own construction risk: the oracle prompt is run as an
isolated pass (full catalogue, judge-only, same discipline as
routing_eval.py's oracle), not hand-scored, but a designer picking cases
toward known targets is not the same instrument as history-sampled cases.

## The prediction

1. **Oracle recall on its own designed target is ~100% by construction** --
   if the oracle does not name the practice each case was written for, the
   case itself is the thing to fix, not evidence about the loader.
2. **Control (all 53 Rules, do-the-work framing) recall on the 8 target
   practices: 80-100%.** These are unambiguous by design; control's
   documented failure mode (attention under task load) should bite less
   than on real, mixed-signal commits.
3. **Treatment (the loader, two hops) recall on the 8 target practices:
   50-75%.** Expected below control, consistent with the existing
   23%-vs-16% gap, but this channel is being tested in its best light (one
   clean occasion per case, nothing competing), so a result at or above
   control here would be a real, specific finding -- not explained away.
4. **If treatment matches or beats control**, that reopens a real question
   the six-round program did not settle: whether the occasion channel is
   fine on clean signals and only degrades on real commits' competing
   signals -- worth a follow-up, not proof the loader is fixed.
5. **If treatment falls clearly below control (>15 points)**, that is a
   second, independent confirmation of the existing finding under
   deliberately favorable conditions, which strengthens rather than
   restates it.

## What would make this run not worth trusting

- Any case where the oracle itself does not name the intended target
  practice -- the case is broken, reported and dropped from the read, not
  silently kept.
- Fewer than 6 of 8 cases scoring (a stalled or malformed answer) --
  reported as a partial run, not extrapolated.

## The result (2026-09-01)

All 8 cases scored (`tools/routing_eval_synthetic.py --score`; raw answers in
`evals/routing_synthetic/answers/`).

| | recall | miss | extras (false positives) |
|---|---|---|---|
| CONTROL (all 53, do-the-work) | 10/10 = 100% | 0% | 3 |
| TREATMENT (the loader, two hops) | 9/10 = 90% | 10% | 1 |

**Two of the eight cases did not survive the oracle validity check named
above, and are dropped from the target read per that stated rule, not
counted as loader misses:** `s05` (a plain boolean support matrix has no
ranking/dominance for `permutation-frontier-column` to act on -- the
resemblance to a cross-product table was surface-only) and `s06` (the
oracle confirmed only `build-buy-decompose`, not the second intended target
`check-source-architecture`). Both arms independently agreed with the
oracle on both -- this is a flaw in this session's case design, not a
loader-vs-control difference.

**On the 6 valid cases, both arms caught their designed-for target 6 of 6
(100%).** The entire recall gap is one miss on `s04`: the oracle also
flagged a second, non-designed-for practice (`affordance-is-shared` -- the
"ship-it" auto-merge trigger fires for any PR commenter, not only the
owner who authorized it) that control's full-catalogue view caught and
treatment's hop-1 never requested by name, so hop-2 never had the Rule to
judge. Precision ran the other way: control added 3 false positives across
two cases, treatment added 1.

**Verdict per the pre-registered reading table: prediction 4 fired, not
prediction 5.** Treatment (90%) landed within a hair of control (100%),
nowhere near the >15-point-below band prediction 5 named, and clears
prediction 3's own stated bar for "a real, specific finding -- not
explained away" (the 50-75% band was not met; treatment beat the top of
it). Read as prediction 4 directs: this does not override the 16%/23%
headline from six rounds on real commits, and 8 designer-picked cases
can't outweigh that -- but it sharpens the diagnosis. The gap on real
commits is not "the occasion channel fails to recognize an occasion when
it is the only signal in front of it" (here, it did, every time). What
this run suggests instead is a second-order failure: a co-applicable
practice riding alongside the obvious one, not requested because hop-1 had
no reason to ask for it by name. That is consistent with, not contrary to,
[spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md)'s own
conclusion that the fix is enforcement (a co-applicable practice with a
working check doesn't depend on being requested) rather than a further
routing-architecture change -- reached here from a different angle, on
different material, and not re-litigating the six-round program's own
closed question.

This is a supplementary check, not a repeat or a rebuttal of the routing_eval.py
program above -- see spec/ATTENTION_CEILING.md for the primary six-round
finding this does not replace.
