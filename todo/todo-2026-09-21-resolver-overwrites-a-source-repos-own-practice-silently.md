---
slug:              todo-2026-09-21-resolver-overwrites-a-source-repos-own-practice-silently
kind:              manual
domain:            engine
severity:          medium
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-21
closed:            null
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

## Closing Condition

Running an engine tool in a source repo, after editing one of that repo's own
practice files, either reflects the edit or **says out loud** that a resolved
clone overrode it and names both paths.
