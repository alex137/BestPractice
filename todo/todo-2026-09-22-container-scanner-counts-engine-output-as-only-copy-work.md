---
slug:              todo-2026-09-22-container-scanner-counts-engine-output-as-only-copy-work
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
noted:             2026-09-22
closed:            null
---
## What

**The archive gate shipped on 2026-09-22 calls this container unsafe over
three clones that hold nothing anyone could lose**, and it will keep saying
so on every reply until something changes.

[tools/precedent_container_safe.py](../tools/precedent_container_safe.py)
excludes engine output by asking
[tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)'s
`classify_dirt()` which dirty paths the refresh wrote. That function marks a
path as engine dirt only when its porcelain code is `M` **and** the path is
in the clone's own `ENGINE_MANIFEST.json`. Two kinds of refresh output miss
that test:

1. **A newly vendored engine file is untracked, not modified.** Adding
   [`precedent_container_safe.py`](../tools/precedent_container_safe.py) to
   `ENGINE_FILES` the same day made the
   refresh write it into every shared source clone, where it arrives as
   `?? tools/precedent_container_safe.py` — manifest-declared, so
   unambiguously the engine's, but classified as a person's dirt.
2. **[`MAP.md`](../MAP.md) is regenerated in each clone and is in no
   manifest list.**
   `engine_owned_paths()` builds its set from `files` (under `tools/`),
   `hook_files` and `ci_workflow_files`; a generated view at the repo root
   is none of those.

Measured 2026-09-22, all three shared source clones identically:

```
/home/user/precedent-shared-writing (main): uncommitted changes, untracked files
    uncommitted: MAP.md
    untracked: tools/precedent_container_safe.py
```

## Why It Matters

The whole argument for the archive gate is that it answers **by looking**
rather than from memory, so a session can trust it over its own
recollection. A gate that is red on every reply for a reason no session can
clear is the failure
[todo-2026-09-21-watermark-commits-pile-up-where-they-cannot-be-pushed](todo-2026-09-21-watermark-commits-pile-up-where-they-cannot-be-pushed.md)
names one paragraph in — **an always-red guarantee teaches sessions to skip
the list** — arriving at the newest check in the repo within a day of it
landing.

## The Options

1. **Widen `classify_dirt()` on both counts**: treat `??` as engine dirt for
   a manifest-declared path (the manifest is a declaration, not a listing of
   what is tracked, so an untracked owned path is the engine's by
   construction), and give the manifest a `generated_views` list carrying
   [`MAP.md`](../MAP.md), [`GLOSSARY.md`](../GLOSSARY.md) and the loader
   block's file. **Recommended** —
   it fixes the classification everywhere it is consulted, not just for the
   scanner, and the dirty-guard in the refresh has the same blind spot.
2. **Exclude generated views in the scanner only.** Cheaper, and it leaves
   the refresh's own guard still unable to tell engine output from a
   person's edit for the same paths.
3. **Leave it.** Cost: the gate is red on every reply in any container that
   holds a source clone, which is most of them.

## Not To Be Confused With

A clone that is genuinely dirty with somebody's edit. The guard
`classify_dirt()` protects is right and must stay — see its own docstring,
and the four sources that drifted for weeks because the tool's output
disarmed the tool.
