---
title:         "Brief: moving the closing-section convention to universal"
kind:          brief
status:        open
opened:        2026-09-14
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       Moves the rule that every reply closes with a Next Steps heading out of one person's individual set and into the universal catalogue, along with the declaration that enforces it — and says what that costs every adopter.
---
# Brief: moving the closing-section convention to universal

**The rule that every reply ends with a real `## Next Steps` heading lives in
one person's individual practice set.** Morgan, 2026-09-14: *"I think we
should move the next steps at the end to be universal, and thus removed from
the individual and team repos."* `strength: decided`.

**This brief is for a session that has all five repositories attached** — this
one and the four practice sets. No session with fewer can do it: the move is
two operations in two different repositories, in order, and a session that can
only reach one end of it will leave a gap where nobody is bound by a rule
everybody still wants.

## What moves, and what deliberately does not

**In scope: one practice, and the declaration that enforces it.**

| Thing | Where it is now | Where it goes |
|---|---|---|
| The practice `next-steps-after-commit` | individual set | `practices/` here |
| The `reply_check.json` entry requiring the heading and the sign-off sentence | individual set root | this repo's own [reply_check.json](../reply_check.json) |

**Out of scope, and say so rather than quietly widening.** The individual set
holds several other practices that shape a reply — how an ask is phrased, what
may appear in the closing list, when a handoff is warranted. **Leave every one
of them where it is.** They were not what was asked for, each needs its own
reach judgment ([rule-level-by-reach](../practices/rule-level-by-reach.md)),
and a move that sweeps up its neighbours is the one nobody can review.

**One practice is genuinely entangled and needs a decision, not a default.**
The sign-off sentence the reply check demands has its *conditions* defined by
a different practice in that same set — the one that says when a session is
finished enough to be archived. Moving the requirement without it leaves a
universal rule demanding a sentence whose meaning is defined privately.
**Decide explicitly, in the pull request body: move both, or move only this
one and write the conditions into the universal practice's own text.** Do not
leave it implicit.

## Why this is two steps and never one

[MOVING_PRACTICES.md](MOVING_PRACTICES.md) is the runbook and it already
covers this exact direction. Follow it rather than improvising:

1. **Land it at universal first** — a pull request here, carrying the existing
   `## Rule`, `## Detail`, `## Why` and `## Story` forward. Real vetted text,
   not re-derived prose.
2. **Then deduplicate the original** — `status: deduplicated`,
   `in_force_at: next-steps-after-commit`, and one line in its `## Story`
   saying where it went. **Never a plain delete**, and never as a side effect
   of step 1.

**Landing first is what makes step 2 checkable**: a correct move passes
through a deliberate moment where both copies exist, so `in_force_at:` has
something real to point at. The reverse order has nothing to name, which is
exactly the state a lost rule is in.

**Keep the slug.** Five files in this repository already name
`next-steps-after-commit`, and reusing it at universal keeps every one of them
correct. A same-slug practice at two levels is an intended override while both
exist, not a collision.

## What this costs every adopter, stated plainly

**The declaration is the half that bites.**
[tools/precedent_reply_check.py](../tools/precedent_reply_check.py) refuses a
turn whose reply misses what a source declared. Today that requirement is
declared by one private set, so it binds one person. Declared here, **it binds
every repository that runs Precedent**: their sessions' replies get refused
without a `## Next Steps` heading and one of the two sign-off sentences.

That is a real, opinionated default and it is the point — a universal practice
nobody enforces is the shape this project just spent a week fixing at the
other end of the engine ([PRACTICE_DETECTION.md](PRACTICE_DETECTION.md)). But
it must be said out loud in the pull request, not discovered by an adopter.

**The engine accumulates declarations, it does not override them.**
`declared_requirements()` collects every source's entry in precedence order
and enforces all of them. So the individual set's entry has to be **removed**
in the same move, not left behind: two identical requirements would both fire,
and `--explain` would report the rule twice with no way to tell which one is
live.

**There is no wording override yet.** Once the phrases are universal, an
adopter who wants different ones has no mechanism but editing the universal
file. If that turns out to matter, it is a follow-up — an `overrides` key on a
declaration — and not a reason to hold this move.

## The payoff worth collecting in the same pass

**Close detection is on for this project and off for every adopter, and this
move switches it on for them too.**
[merged-session-offers-a-practice](../practices/merged-session-offers-a-practice.md)
fires only when a source declares a `close_detect.json` naming its
ready-to-archive sentence. Since 2026-09-14 one source does — Morgan's
individual set, whose declaration landed once a session holding both owners
could push it
([TODO.md's `close-detect-declaration-unpushed` item](../todo/todo-2026-09-14-close-detect-declaration-unpushed.md),
now closed). Nobody else's does, and nothing tells them to.

**Once the sign-off sentence is universal, that file can be universal too** —
declared in this repository, next to `reply_check.json`, so an adopter gets
close detection by installing Precedent rather than by knowing to write five
keys. Do it in the same pull request; the practice's `## Install` section
carries the content verbatim, and the individual set's copy then becomes the
override case rather than the only one.

## Before opening the pull request

- **Regenerate the views.** A new practice file changes the loader block, the
  occasion index and [MAP.md](../MAP.md), all built by
  [tools/build_views.py](../tools/build_views.py).
- **Watch the load budget.** [AGENTS.md](../AGENTS.md) sits close to its declared ceiling and
  this adds an occasion-index line. `python3 tools/precedent_check.py --only
  session-load-budget` says whether it still fits; if not, run a reduction pass
  rather than raising the number.
- **Repoint the stale example.**
  [tools/precedent_reply_check.py](../tools/precedent_reply_check.py)'s
  docstring uses this very requirement as its example of something *a source
  declares rather than the engine shipping*. That sentence stops being true the
  moment the engine's own source declares it. Rewrite it; do not delete the
  distinction, which still holds for every other requirement.
- **Deep check in each repository it touches**, per that repository's own
  rules. Here that is the five-gate suite
  [AGENTS.md](../AGENTS.md) names under "Two check levels", and `0 failed` /
  `0 violated` is what matters — never a passed count.
- **Base branch is `precedent-beta-v01`**, never `main`.

## How to know it worked

From a fresh session in any repository running Precedent:

```
python3 tools/precedent_reply_check.py --explain
```

It should name the universal source as the one declaring the heading and the
sign-off sentence, and **should not name the individual set at all**. If both
appear, step 2 did not happen.
