---
slug:              todo-2026-09-21-resolver-overwrites-a-source-repos-own-practice-silently
kind:              manual
domain:            engine
severity:          medium
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "local file wins, collision named, --resolved-view restores the old precedence"
decision_strength: assented
waiting_on:        null
noted:             2026-09-21
closed:            2026-09-22
---
## What

**In a repo that is itself a practice source, the engine tools read that repo's
own `practices/` and then silently throw the answer away.**
[tools/precedent_vocabulary.py](../tools/precedent_vocabulary.py)'s `collect()`
loads every local `practices/*.md`, then loops over what
[tools/precedent_resolve.py](../tools/precedent_resolve.py) returns and assigns
`found[slug] = ...` with no guard. For a consuming repo that precedence is
right. For a **source** repo the two halves are the same practice, resolved
from a different checkout, and the local edit loses without a word.

The measured cost is in
[the gotcha](../gotchas/gotcha-2026-09-21-editing-a-practice-in-its-own-source-repo-does-not-change-the-tools-answer.md):
a session edited a practice, ran the tool to confirm, and got the old value,
with every other check agreeing the edit was fine.

## The Fix Worth Making

**One line of output where the overwrite happens.** When a resolved source's
path is not the repository the tool is running in, and that source supplies a
slug the local `practices/` also defines, say so — which slug, which two paths,
which one won. Silence is the whole defect; the precedence itself is defensible.

Worth deciding at the same time: whether **local should win** in that case. A
session editing a practice in its own source repo is almost always asking about
the edit in front of it, not about whatever a cached clone holds. Reversing the
precedence would be a bigger change and might surprise a tool run from a source
repo that legitimately wants the resolved view, which is why this is filed
rather than done.

## Where Else It Bites

`collect()` is the measured case and is unlikely to be the only one. Any tool
that merges a local catalogue with a resolved one has the same shape. Before
fixing, grep for the pattern rather than patching the one call site
([fix-the-original](../practices/fix-the-original.md)).

## It Was Two Defects, And They Closed Separately

**(a) STALENESS -- the resolved clone was behind.** Closed by
[`febfcf5191`](https://github.com/alex137/BestPractice/commit/febfcf5191)
("Make the source clone current first, and stop a skip reporting success"),
2026-09-21, which reworked
[tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py) to
bring source clones current at session start. Unrelated work; it closed this
half as a side effect. **Left joined to (b), the next reader tests the fixed
half, sees it pass, and closes the whole item while (b) is still there** --
which is why this section exists.

**(b) SHADOWING -- the local file lost to a resolved copy, in silence.**
Closed 2026-09-22 by the change described below.

## What The Measurement Actually Showed, 2026-09-22

**The reproduction did not reproduce, and that is worth recording rather than
arguing with.** A probe `command:` added to an uncommitted practice in the
individual source came straight through the tool. The reason: on this
container the resolver's path for that source **is** the directory being
edited, so "local" and "resolved" are the same file and there is nothing to
shadow. What 2026-09-21 had, and this container no longer has, is a second
checkout — the condition the duplicate-clone work of 2026-09-22 morning also
attacks from its own side.

**The code defect was real regardless, and was proven directly.** Run against
a planted two-checkout fixture, the old `collect()` returned the stale phrase
and **no notes at all**. Not a wrong answer with a caveat — a wrong answer
with nothing to read.

**The blast radius is one merge point, measured rather than assumed.** Sixteen
tools import both `precedent_resolve` and a local `practices/` path; every one
of them except `collect()` reads `res['practices']` **exclusively** and never
builds a local half to be overwritten. [`build_views.py`](../tools/build_views.py), [`precedent_gate.py`](../tools/precedent_gate.py),
[`precedent_session_practices.py`](../tools/precedent_session_practices.py), [`full_practice_audit.py`](../tools/full_practice_audit.py) and
[`precedent_materialize.py`](../tools/precedent_materialize.py) were each read at their merge line. There is no
second call site to fix.

## What Landed

**The local file wins, and the collision is named either way.** Where a
resolved practice for a slug comes from a different file than the local one,
[tools/precedent_vocabulary.py](../tools/precedent_vocabulary.py) keeps the
local **content** and the resolved **label** — a local read cannot know
whether it is standing in a universal, shared or individual set, and the
resolver does — then prints one line naming the slug, both paths and the
winner. `--resolved-view` restores the old precedence for a caller that
genuinely wants it: a flag, not a silent default.

Six stated cases in [tools/verify_harness.py](../tools/verify_harness.py),
planted rather than run against the real disk, because whether a given
container is in the two-checkout state changes with its config and a check
that only fires on a misconfigured machine is a check that reports the
weather. The two negative controls carry it: a slug only the resolver has
still comes from there, and `--resolved-view` still reaches the old answer.

**Not done here, and not a follow-up this repository can perform:**
[`precedent_vocabulary.py`](../tools/precedent_vocabulary.py) is a vendored engine file, so no consuming repo gets
this until it takes an `Update Vendors` pass. Those repositories are under a
different owner and cannot be reached from a session rooted here.

## Closing Condition

Running an engine tool in a source repo, after editing one of that repo's own
practice files, either reflects the edit or **says out loud** that a resolved
clone overrode it and names both paths.
