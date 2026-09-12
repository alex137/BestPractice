---
slug:        fix-the-original
title:       Fix the original, not just the copy in front of you
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "fixing a file that came from somewhere else -- a template, a vendored tree, another repo's copy"
index_clause: "fix the origin first, then every copy -- name them all in the reply"
gates:       ["review", "reply"]
checked_by:  null
defines:     ["the origin artifact"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-12"
approved_by: "Morgan, 2026-09-12"
strength:    decided
---
## Rule
**A file you are fixing may be a copy, and the copy is never the whole
job.** Before reporting any fix done, answer two questions out loud:

1. **Where did this file come from?** A template it was instantiated from, a
   vendored tree it was copied out of, another repo that had it first.
2. **Who else has a copy?** Every other place the same file, or the same
   mistake, was propagated to.

**The fix goes to the origin first**, then to the copies, and **the reply
names all of them.** If the origin cannot be reached from this session, that
is a `blocked-on` item naming the repository — never a silent omission.

Both questions are answerable with one search. That is deliberate: this is a
lookup, not a meditation on root causes. **A session that cannot find an
origin in one search says so and moves on.**

## Detail
**This is a different axis from the three practices that look like it**, and
the gap between them is where the failure lives:

| Practice | Asks | Blind to |
|---|---|---|
| [durable-fix](durable-fix.md) | *Where does the fix live?* | How many copies exist. A downstream repo's edited copy is a committed file, so it scores rung 1 and passes. |
| [generated-edit-goes-upstream](generated-edit-goes-upstream.md) | *Is this file generated?* | A file nothing regenerates. An instantiated copy is not a render, so this never fires on it. |
| [mistakes-become-rules](mistakes-become-rules.md) | *What rule prevents the next one?* | The artifact itself. A rule can be written while the template stays broken. |

**The case this exists for is the instantiated copy**: a file born from a
template or copied between repos, that nothing regenerates and no manifest
tracks. It is invisible to all three above by construction.

**"The same mistake" counts, not only the same file.** A wrong argument
copied into five hooks is one origin and five copies even where the five
files are otherwise unrelated.

**On the mechanical check, which was attempted and declined with a reason**
([checkable-gets-checked](checkable-gets-checked.md) requires the attempt,
not the outcome). Two designs were built and run against this tree on
2026-09-12:

- **Same-basename divergence across the repo and every attached source**
  reported **12 identical and 100 divergent** basenames. Nearly all of the
  100 are correct work — per-case test fixtures that are *supposed* to
  differ, and per-source `approvers.json` files whose whole purpose is to
  differ. A check that fires on a hundred correct files teaches the next
  session to ignore the gate.
- **Template-to-instantiation similarity**, narrowed to `templates/` against
  the rest of the tree, was far cleaner: **six pairs**, four identical and
  two divergent. But both divergences are legitimate and **each instance
  already documents why it differs from its template in its own header** —
  so the check would be red on the unplanted tree from the day it landed.

**The reason no check is wired is therefore specific: divergence is not the
signal.** A copy that legitimately differs and a copy that drifted are
identical to a differ, and nothing in the tree records which is which.
**The checkable version of this practice is a provenance stamp**, not a
similarity threshold — and that is a real design, not a shrug, filed in
[TODO.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/TODO.md).
The one family that *does* carry provenance is already checked:
[tools/precedent_refresh_sources.py](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/tools/precedent_refresh_sources.py)
compares each source's vendored engine against canonical, which is why
engine staleness reaches a person at session start and template drift does
not.

## Why
**The cost is paid in a different repository from the one that saves it**,
which is why no single session ever sees it. Fixing the copy in front of you
genuinely solves your problem; the recurrence lands on someone else, months
later, looking like a new bug because its surface details are new.

**The person watching is the only one who can see it**, and that is the
failure mode worth naming: the signal that this practice is missing is a
human having to say *"also change it in the template"* — repeatedly, across
unrelated threads, because each session in isolation was correct.

## Story
**Requested by Morgan, 2026-09-12, in those terms:** *"I often have to
remind you, make this change not just in this file, but in the original
template that led to it."* He described the general shape too — a fix
applied once, in one repo, while the cause stays free to fire again
elsewhere.

**This repository had already paid for it twice, and recorded both without
generalising either.** `commit-identity.sh` was found **one version behind
in all five** real private practice sets — uniform drift, which is what a
template fix that never went back to the template looks like from the
outside. One of those sets' `freshness-guard.sh` was about three thousand
bytes shorter than canonical, supporting two modes where the current file
supports three.

**What was built in response was a repair path, not a prevention.**
`precedent_refresh_sources.py --apply` restores a drifted hook, and the
session that wrote it recorded the asymmetry precisely: *"there was an
install path and no repair path."* Both are downstream of the copy already
having diverged. **Nothing asked, at the moment of the fix, where the file
came from** — and that moment is the only one at which the drift costs
nothing to prevent.

## Install
Two questions before any fix is reported, and one line in the reply.

- **Search for the origin.** `grep -rl "<a distinctive line from the file>"`
  across the repo and any attached sources, or check whether a `templates/`
  copy of the same basename exists.
- **Fix the origin first**, then the copies. Doing it in that order is what
  keeps the copies from being forgotten once the visible symptom is gone.
- **Name every file in the reply**, per
  [reply-links-files](reply-links-files.md). A fix that touched an origin
  and three copies is four entries, not one.
- **Where the origin is out of reach**, say so in those words and queue it
  per [todo-is-a-handoff](todo-is-a-handoff.md) with the repository named —
  the same `blocked-on` reasoning
  [cross-source-rollout](cross-source-rollout.md) already uses.
