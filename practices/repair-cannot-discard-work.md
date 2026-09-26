---
slug:        repair-cannot-discard-work
title:       A repair that can discard work is not a repair
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "writing or changing anything that automatically repairs a state it found wrong"
gates:       []
index_clause: "an auto-repair must never discard work; reporting is not repairing"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-22"
approved_by: "Morgan F, 2026-09-22 (strength: decided)"
---
## Rule
**Anything that automatically repairs a state it found wrong must be
incapable of destroying work in the process.** Where a repair has a variant
that keeps both sides and a variant that replaces one with the other, take
the one that keeps both -- and where neither is available, stop and leave
the state exactly as it was rather than half-applying a fix.

**And reporting the problem is not repairing it.** A mechanism that detects
the wrong state, announces it, and leaves it there has not solved anything:
the state persists, every subsequent run announces it again, and a person
ends up doing by hand the thing the mechanism exists to do. A detector that
never repairs is a detector, and should be described as one rather than
counted as the fix.

**The two halves are one rule because they trade against each other, and
the trade is where this goes wrong.** The tempting move, once a repair has
destroyed something, is to switch the repair off and keep the detection.
That feels like the cautious choice and it is not: it swaps a rare, loud
failure for a constant, quiet one. The right move is to keep repairing and
make the repair safe.

## Why
A repair runs unattended, which is the whole point of it, and that is also
exactly why it cannot be allowed to make an unrecoverable choice. The person
it runs for is not watching, has no chance to object, and in the ordinary
case will not find out. So the bar is not "usually right" -- it is "cannot
lose anything even when wrong."

The second half exists because the first half, taken alone, has an obvious
and wrong escape hatch. Faced with a repair that might destroy something,
the cheapest change is always to stop repairing. It passes every test the
first half sets, and it is how a working mechanism becomes a nagging one.

## Install
When you are about to ship something that fixes a state automatically, ask
two questions before it goes anywhere:

- **Can this repair lose something the person had?** List what it overwrites,
  resets, deletes or replaces. If the answer is anything but "nothing", find
  the variant that keeps both sides -- and if there is none, make the failure
  path leave the state untouched rather than partly changed.
- **If it cannot repair, what does it do?** "Prints a warning" is an answer
  that needs a reason. Say who acts on that warning and when. If the honest
  answer is "the person, eventually, by hand", the mechanism is a detector,
  and saying so is better than counting it as the fix.

And when a repair HAS destroyed something and you are deciding what to do
about it: the change to reach for is the safer repair, not switching the
repair off.

## Story
[`.claude/hooks/freshness-guard.sh`](https://github.com/alex137/BestPractice/blob/staging/.claude/hooks/freshness-guard.sh)
repairs a checkout that has drifted from its remote. On 2026-09-20 the
mid-session path did that with `git reset --hard`, which destroyed a real
unpushed commit; it was recovered only because a rescue ref and the reflog
both happened to still hold it
([the gotcha](https://github.com/alex137/BestPractice/blob/staging/gotchas/gotcha-2026-09-20-freshness-guard-s-user-prompt-mode-hard-resets-a-mid-sess.md)).

The fix that day cut that path back to a warning -- correct about the
danger, wrong about the remedy, and it took the escape hatch this rule
names. Two days later the cost arrived: the drift simply stayed, every
prompt re-announced it, and Morgan reported the original problem as having
come back. What was actually needed was available the whole time -- a merge
keeps both sides' commits, so it cannot discard local work the way the reset
could, and a merge that conflicts can be aborted rather than half-applied.

Landed narrowed, on purpose. The wider version proposed in
[issue #536](https://github.com/alex137/BestPractice/issues/536) also said
that a session must verify its checkout before its first write -- which is a
description of what a script already does, not a judgment anyone applies.
Morgan, 2026-09-22 (strength: decided): keep the half that needs judgment,
drop the half that restates the code.
