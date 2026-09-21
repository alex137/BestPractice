---
slug:              todo-2026-09-21-two-tools-generate-agents-md-and-disagree
kind:              manual
domain:            engine
severity:          high
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Option 1 -- one renderer: both callers ask bv.placed_practice_file() where a practice lives"
decision_strength: decided
waiting_on:        null
noted:             2026-09-21
closed:            2026-09-21
---
## What

**[tools/precedent_sync_views.py](../tools/precedent_sync_views.py) and
[tools/build_views.py](../tools/build_views.py) both generate
[AGENTS.md](../AGENTS.md)'s
loader block, and they rewrite sibling practice links differently.** The
installer runs the first; `generated-artifact-provenance` runs the second.
So a freshly installed project fails its own provenance check from the
moment it is created.

Reduced to one line, in a scratch install with every `PRECEDENT_*` unset and
`HOME` pointed at an empty directory:

```
precedent_sync_views.py writes:  [My options](practices/my-options.md)
build_views.py --check wants:    [My options](precedent/universal/practices/my-options.md)
```

`build_views --check` then reports [AGENTS.md](../AGENTS.md) as
"hand-edited or stale".
Nobody hand-edited anything.

## Why It Went Unseen

Three layers, each of which reads as a different problem:

1. **The check is rotation-gated.** A plain
   [precedent_check.py](../tools/precedent_check.py) run reports
   `generated-artifact-provenance` among the "tree-scope check(s) not run
   this invocation". It only surfaces under `--full-sweep`, or when the
   rotation slice happens to include it — which is why a first reproduction
   attempt came back clean and looked like the bug was gone.
2. **An undeclared individual source contaminated the diff.** Regenerating
   in the scratch project pulled in three INDIVIDUAL practices the project's
   own `precedent.json` never declares (it declares universal and
   repo-local only), producing a large alarming diff that masked the real
   one-line cause. That is a second finding in its own right: see below.
3. **The trigger is recent.** `fence-block-for-paste` became a RESIDENT
   practice in `de72bc56` (2026-09-21) and carries a sibling-relative link,
   `[My options](my-options.md)`. Resident practices render into the loader
   block, so that commit is what first exposed the disagreement. It has been
   red on `precedent-beta-v01` ever since — through eight merges that day,
   each of which had to read past it.

## Why It Matters

A gate that never reads clean is a gate nobody reads. Every deep check that
day required a human to decide which failures were new, and that
interpretation cost two near-misses in one session — a planted case silently
disarmed, and an over-corrected `--structural-only` — both caught only
because somebody looked carefully at output they had already been told to
expect.

## What Would Close It

**One tool generates the artifact.** Which rewrite is correct is the
decision; the duplication is the bug. Candidates:

1. [precedent_sync_views.py](../tools/precedent_sync_views.py) calls
   [build_views.py](../tools/build_views.py) rather than carrying its
   own renderer, so there is one implementation and no way to disagree.
2. Keep both, and add a check asserting they produce byte-identical output
   for the same tree — cheaper to write, and it only detects the next
   divergence rather than preventing it.

Option 1 is what `registry-source-of-truth` already says about state, and
the same argument applies to a renderer.

**Separately, and worth its own answer:** why does regenerating in a project
that declares only `universal` and `repo-local` resolve an INDIVIDUAL source
at all? Either the resolution is reaching past the project's declared
sources, or the project's declaration is not what constrains it. Nobody has
established which.

## How It Was Closed (2026-09-21)

**Option 1, on Morgan's explicit pick** — *"My pick is
[precedent_sync_views.py](../tools/precedent_sync_views.py) calling [build_views.py](../tools/build_views.py) so there's one renderer
and no way to disagree"* (`decided`, quoted).

The two were already calling the same `build_loader_block()`. The
disagreement was one argument: the **file path** each passed for a practice,
which is what `_place_rule_links` resolves a sibling citation against.
[precedent_sync_views.py](../tools/precedent_sync_views.py) passed the materialized path,
[build_views.py](../tools/build_views.py) passed the source clone's. Both exist on disk in a consuming repo, so
neither was reported unplaceable — they simply rendered differently.

[`build_views.placed_practice_file()`](../tools/build_views.py) is now the
one place that answers it, and both callers ask it. Verified in the scratch
install this item was reduced in, both ambient and with `HOME` emptied and
every `PRECEDENT_*` unset: the install step writes [AGENTS.md](../AGENTS.md),
and
`precedent_check.py --full-sweep --only generated-artifact-provenance` comes
back `1 passed, 0 violated`. BestPractice's own tree is byte-identical
before and after, which is the no-regression case — here `practices/` IS the
universal source's directory, so the two paths were always the same one.

**The second question above is NOT closed by this**, and is filed on its own:
[todo-2026-09-21-scratch-install-resolved-an-undeclared-individual-source.md](todo-2026-09-21-scratch-install-resolved-an-undeclared-individual-source.md).
