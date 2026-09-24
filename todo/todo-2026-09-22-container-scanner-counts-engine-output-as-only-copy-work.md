---
slug:              todo-2026-09-22-container-scanner-counts-engine-output-as-only-copy-work
kind:              manual
domain:            engine
severity:          medium
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "option 1 -- widen classify_dirt on both counts"
decision_strength: assented
waiting_on:        null
noted:             2026-09-22
closed:            2026-09-22
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

## What Was Done, 2026-09-22

**Option 1, both halves.** Morgan: *"Go update on the container scanner false
positive"* — a go-ahead to this item's own recommendation rather than a
choice he argued for, so `assented`.

[`classify_dirt()`](../tools/precedent_refresh_sources.py) now counts `??`
as engine dirt for a manifest-declared path. The manifest is a
**declaration** of what the engine writes, not a listing of what git has
seen, so a path it names is the engine's whether the clone has tracked it
before or not — and that manifest's own `_note` already tells people never
to hand-write a file it lists.

`engine_owned_paths()` now also claims the fully generated views. The names
come from [`build_views.py`](../tools/build_views.py)'s new
`FULLY_GENERATED_VIEWS` rather than being repeated, read lazily so a
vendored engine that arrived without that module still classifies
everything the manifest names. **[`AGENTS.md`](../AGENTS.md) is deliberately not
among them**: only its loader block is generated and the rest is somebody's
prose, so a modified copy of it stays a person's file.

**Widening the classification meant widening the discard.** `git checkout
--` fails outright on a path git has never tracked, so `make_current()`
would have turned a working refresh into a refusal. A new
`discard_engine_dirt()` restores the tracked ones and **removes** the
untracked ones — the refresh that immediately follows rewrites every path
in that set, so the file is back, from upstream, in the same run.

Measured after the change, on the three real clones: `other: []` on all
three, and the scanner drops from 4 unsafe checkouts to the 2 that hold
genuine work. Twelve more stated cases in
[tools/verify_harness.py](../tools/verify_harness.py) — nineteen in that
check now — including the negative controls that an untracked file the
manifest does **not** name is still a person's, and that the two kinds of
engine dirt take different routes.

## Not To Be Confused With

A clone that is genuinely dirty with somebody's edit. The guard
`classify_dirt()` protects is right and must stay — see its own docstring,
and the four sources that drifted for weeks because the tool's output
disarmed the tool.
